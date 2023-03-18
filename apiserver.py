from flask import Flask, jsonify, request
import subprocess
import requests
import asyncio

app = Flask(__name__)

class Server:
    def __init__(self):
        # Port to listen to
        self.port = 5555
        # Path to llama.cpp executable
        self.llamacpp_path = './main'
        # Path to the model to use
        self.model_path = './models/7B/ggml-model-q4_0.bin'
        # How many thread to use
        self.threads = 8;
        # Announces maximum context length to api
        self.max_context_length = 1024
        # Announces max length (to generate) to api
        self.max_length = 80
        
        # Announces this model name to the api
        # (Use 'Pygmalion/pygmalion-6b' for TavernAI)
        self.model_announce = 'Pygmalion/pygmalion-6b'
        
        # Announces current softprompt to api (Unused)
        self.softprompt = ''
        # Announces a list of softprompts to api (Unused)
        self.softprompts_list = []
        # Show output as a string representation of an object.
        self.repr_output = True
        # Don't change, users need to know if we're busy
        self.busy = False

    # API - generate
    @app.route('/api/latest/generate/', methods=['POST'])
    @app.route('/api/v1/generate/', methods=['POST'])
    @app.route('/api/generate/', methods=['POST'])
    def generate():
        # 503, we're already generating something
        if server.busy:
            return jsonify({
                'detail': {
                    'msg': 'Server is busy; please try again later.',
                    'type': 'service_unavailable'
                }
            }), 503
        
        # Run - generate_async
        result = asyncio.run(server.generate_async(request.json))
        return result

    # API - model
    @app.route('/api/latest/model/', methods=['GET'])
    @app.route('/api/v1/model/', methods=['GET'])
    @app.route('/api/model/', methods=['GET'])
    def get_model():
        if request.method == 'GET':
            return jsonify({'result': server.model_announce}), 200
        elif request.method == 'PUT':
            return jsonify({}), 200

    # API - /config/max_content_length
    @app.route('/api/latest/config/max_context_length/', methods=['GET', 'PUT'])
    @app.route('/api/v1/config/max_context_length/', methods=['GET', 'PUT'])
    @app.route('/api/config/max_context_length/', methods=['GET', 'PUT'])
    def get_max_context_length():
        if request.method == 'GET':
            return jsonify({'value': server.max_context_length}), 200
        elif request.method == 'PUT':
            return jsonify({}), 200
        
    # API - /config/max_length
    @app.route('/api/latest/config/max_length/', methods=['GET', 'PUT'])
    @app.route('/api/v1/config/max_length/', methods=['GET', 'PUT'])
    @app.route('/api/config/max_length/', methods=['GET', 'PUT'])
    def get_max_length():
        if request.method == 'GET':
            return jsonify({'value': server.max_length}), 200
        elif request.method == 'PUT':
            return jsonify({}), 200

    # API - /config/soft_prompt
    @app.route('/api/latest/config/soft_prompt/', methods=['GET', 'PUT'])
    @app.route('/api/v1/config/soft_prompt/', methods=['GET', 'PUT'])
    @app.route('/api/config/soft_prompt/', methods=['GET', 'PUT'])
    def get_soft_prompt():
        if request.method == 'GET':
            return jsonify({'value': server.softprompt}), 200
        elif request.method == 'PUT':
            return jsonify({}), 200
        
    # API - /config/soft_prompts_list
    @app.route('/api/latest/config/soft_prompts_list/', methods=['GET'])
    @app.route('/api/v1/config/soft_prompts_list/', methods=['GET'])
    @app.route('/api/config/soft_prompts_list/', methods=['GET'])
    def get_soft_prompts_list():
        return jsonify({'values': server.softprompts_list}), 200

    # generate_async - Returns what llama.cpp generates, eventually
    async def generate_async(self, data):
        command_args = []
        print_args = []

        # Grab what we need, set defaults for others
        max_length = data.get('max_length', 80)
        command_args.extend(['-n', str(max_length)])
        
        max_context_length = data.get('max_context_length', 1024)
        command_args.extend(['-c', str(max_context_length)])

        temp = data.get('temperature', 0.8)
        command_args.extend(['--temp', str(temp)])

        rep_pen = data.get('rep_pen', 1.3)
        command_args.extend(['--repeat_penalty', str(rep_pen)])
        
        # Uncomment to use, results may be very unpredictable.
        #top_k = data.get('top_k', 40)
        #command_args.extend(['--top_k', str(top_k)])

        #top_p = data.get('top_p', 0.9)
        #command_args.extend(['--top_p', str(top_p)])

        #rep_pen_range = data.get('rep_pen_range', 64)
        #command_args.extend(['--repeat_last_n', str(rep_pen_range)])
        
        print_args = command_args.copy()
        prompt = data.get('prompt', '').replace('\r\n', '\n')
        command_args.extend(['-p', prompt])

        # Construct full command
        command = [server.llamacpp_path, '-m', server.model_path, '-t', str(server.threads)] + command_args
        # Print PROMPT
        if server.repr_output:
            print('[PROMPT] \033[93m' + repr(prompt) + '\033[0m')
        else:
            print('[PROMPT] \033[93m' + prompt + '\033[0m')
        print('[ARGS] \033[92m' + str(print_args) + '\033[0m') # Print ARGS

        server.busy = True # We're busy
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        
        if process.returncode != 0:
            return jsonify({
                'detail': {
                    'msg': 'Error generating response.',
                    'type': 'server_error'
                }
            }), 500
        
        # Windows specific: \r\r\n to \r\n
        output_str = stdout.decode('utf-8').replace('\r\n', '\n')
        output_str = output_str.replace(prompt, '')
        
        # Print OUTPUT
        if server.repr_output:
            print('[OUTPUT] \033[94m' + repr(output_str) + '\033[0m')
        else:
            print('[OUTPUT] \033[94m' + output_str + '\033[0m')
        
        server.busy = False # Not busy
        return jsonify({'results': [{'text': output_str}]}), 200

# Do things
server = Server()

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=server.port
    )
    
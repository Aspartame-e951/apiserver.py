from flask import Flask, jsonify, request
import subprocess
import requests
import asyncio

app = Flask(__name__)

class Server:
    def __init__(self):
        # Port to listen to
        self.port = 5555
        # Path to main executable
        self.main_path = './main'
        # Path to the model to use
        self.model_path = './models/llama-13b-ggml-q8_0.bin'
        # Announces this model name to the api
        self.model_announce = 'llama-13b-ggml-q8-0'
        # How many thread to use
        self.threads = 8;
        # Announces maximum context length to api
        self.max_context_length = 1024
        # Announces max length (to generate) to api
        self.max_length = 80
        # Ignore EOS and keep on generating?
        self.ignore_eos = False
        # GPU layer offloading (0 to disable)
        self.gpu_layers = 60
        # Announces current softprompt to api (Unused)
        self.softprompt = ''
        # Announces a list of softprompts to api (Unused)
        self.softprompts_list = []
        # Show output as a string representation of an object.
        self.repr_output = False
        # Don't change, users need to know if we're busy
        self.busy = False

    # API - api
    @app.route('/', methods=['GET'])
    @app.route('/api/', methods=['GET'])
    def get_api():
        if request.method == 'GET':
            return jsonify({'result': 'apiserver.py'}), 200
        
    # API - version
    @app.route('/api/latest/info/version/', methods=['GET'])
    @app.route('/api/v1/info/version/', methods=['GET'])
    @app.route('/api/info/version/', methods=['GET'])
    def get_version():
        if request.method == 'GET':
            return jsonify({'result': '1.0'}), 200
        
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
        command_args.extend(['--n-predict', str(max_length)])
        
        max_context_length = data.get('max_context_length', 1024)
        command_args.extend(['--ctx-size', str(max_context_length)])

        temp = data.get('temperature', 0.8)
        command_args.extend(['--temp', str(temp)])

        rep_pen = data.get('rep_pen', 1.1)
        command_args.extend(['--repeat_penalty', str(rep_pen)])
        
        top_k = data.get('top_k', 40)
        command_args.extend(['--top-k', str(top_k)])

        top_p = float(data.get('top_p', 0.9))
        if top_p <= 0:
            top_p = 0.001
        command_args.extend(['--top-p', str(top_p)])
        
        tfs = data.get('tfs', 1.0);
        command_args.extend(['--tfs', str(tfs)])
        
        typical = data.get('typical', 1.0);
        command_args.extend(['--typical', str(typical)])

        rep_pen_range = data.get('rep_pen_range', 1024)
        command_args.extend(['--repeat-last-n', str(rep_pen_range)])
        
        if server.gpu_layers > 0:
            command_args.extend(['--n-gpu-layers', str(server.gpu_layers)])
        
        if server.ignore_eos:
            command_args.extend(['--ignore-eos'])
        
        print_args = command_args.copy()
        prompt = data.get('prompt', '').replace('\r\n', '\n').encode('utf-8', errors='ignore')
        command_args.extend(['--prompt', prompt])
        
        # Construct full command
        command = [server.main_path, '--model', server.model_path, '--threads', str(server.threads)] + command_args
        # Print PROMPT
        if server.repr_output:
            print('[PROMPT] \033[93m' + repr(prompt) + '\033[0m')
        else:
            print('[PROMPT] \033[93m' + prompt + '\033[0m')
        print('[ARGS] \033[92m' + str(print_args) + '\033[0m') # Print ARGS

        server.busy = True # We're busy
        # The easy way out
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()

            if process.returncode != 0:
                print('[ERROR] \033[91m' + 'returncode != 0' + '\033[0m')
                server.busy = False # Not busy
                return jsonify({
                    'detail': {
                        'msg': 'Error generating response.',
                        'type': 'server_error'
                    }
                }), 500
            
            output_str = str(stdout.decode('utf-8', errors='ignore').replace('\r\n', '\n'))
            if len(output_str) > len(prompt)-1:
                #output_str = output_str[len(prompt)-1:]
                output_str = str(output_str)[1:].replace(prompt, '');

            # Print OUTPUT
            if server.repr_output:
                print('[OUTPUT] \033[94m' + repr(output_str) + '\033[0m')
            else:
                print('[OUTPUT] \033[94m' + output_str + '\033[0m')

            server.busy = False # Not busy
            return jsonify({'results': [{'text': output_str}]}), 200
        except Exception as e:
            print('[ERROR] \033[91m' + str(e) + '\033[0m')
            server.busy = False # Not busy
            return jsonify({
                'detail': {
                    'msg': 'Error generating response.',
                    'type': 'server_error'
                }
            }), 500
        
# Do things
server = Server()

if __name__ == '__main__':
    app.run(
        host = '0.0.0.0',
        port = server.port
    )

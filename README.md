# apiserver.py

A small standalone flask python server for llama.cpp that acts like a KoboldAI api.

## Description

Receives and returns json data. Due to llama.cpp's current implementation, models don't stay in memory and interate over the entire prompt which extends generation times from prompt to prompt.

Done just for the sake of curiosity.

## How to use

Edit apiserver.py in a text editor to configure it. Start by running apiserver.py through the command line or apiserver.bat (for Windows users). Plug it into a frontend and you're good to go.

```
python apiserver.py
```


This would make Tavern use Pygmalion's prompt for LLaMA models:
```
self.model_announce = "Pygmalion/pygmalion-6b"
```

---

```
/api/generate/
/api/v1/generate/
/api/latest/generate/

POST
{
  "prompt": "Hello world.",
  "max_length": 80,
  "temperature": 0.8,
  "rep_pen": 1.3,
  "top_k": 40,
  "top_p": 0.9,
  "rep_pen_range": 64
}

Response 200
{
  "results": [
    {
      "text": " Hello."
    }
  ]
}

Response 503
{
  "detail": {
    "msg": "Server is busy; please try again later.",
    "type": "service_unavailable"
  }
}

Response 500
{
  "detail": {
    "msg": "Error generating response.",
    "type": "service_error"
  }
}
```

```
/api/model/
/api/v1/model/
/api/latest/model/

GET 200
{
  "result": "Facebook/LLaMA-7b"
}
```

```
/api/config/max_context_length/
/api/v1/config/max_context_length/
/api/latest/config/max_context_length/

GET 200
{
  "value": 1024
}

PUT 200
{}
```

```
/api/config/max_length/
/api/v1/config/max_length/
/api/latest/config/max_length/

GET 200
{
  "value": 80
}

PUT 200
{}
```

```
/api/config/soft_prompt/
/api/v1/config/soft_prompt/
/api/latest/config/soft_prompt/

GET 200
{
  "values": ""
}

PUT 200
{}
```

```
/api/config/soft_prompts_list/
/api/v1/config/soft_prompts_list/
/api/latest/config/soft_prompts_list/

GET 200
{
  "value": []
}

PUT 200
{}
```

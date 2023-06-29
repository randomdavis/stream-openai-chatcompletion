import openai


def stream_ai_function_response(response):
    printed_keys = []
    for chunk in response:
        text = chunk['choices'][0]['delta'].get('content', '')
        function_call_data = chunk['choices'][0]['delta'].get('function_call', None)
        if text:
            yield text
        if function_call_data:
            for key, value in function_call_data.items():
                if key not in printed_keys:
                    printed_keys.append(key)
                    yield f"\n\n{key}:\n{value}"
                else:
                    yield value


with open('apikey.txt', 'r') as f:
    API_KEY = f.read().strip()

openai.api_key = API_KEY

messages = [{
    "role": "user",
    "content": "Tell me a one sentence story with two personalities, kind and sarcastic, about a brave adventurer."
}]
functions = [{
    "name": "get_varied_personality_responses",
    "description": "Ingest the various personality responses",
    "parameters": {
        "type": "object",
        "properties": {
            "kind": {"type": "string", "description": "A kind and helpful version of the response"},
            "sarcastic": {"type": "string", "description": "A sarcastic version of the response"}
        },
        "required": ["kind", "sarcastic"]
    }
}]
response = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=messages, functions=functions, function_call="auto", stream=True)

print("Function response:")

for output in stream_ai_function_response(response):
    print(output, end='')

messages = [{
    "role": "user",
    "content": "Instead of responding with something that's kind and helpful or sarcastic, instead just list the top 3 ways to beat the heat this summer."
}]

response = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=messages, functions=functions, function_call="auto", stream=True)

print("\nRegular text response:")

for output in stream_ai_function_response(response):
    print(output, end='')

import openai

with open('apikey.txt', 'r') as f:
    API_KEY = f.read().strip()

openai.api_key = API_KEY


def stream_chat_completion(prompt: str, model: str = 'gpt-3.5-turbo', temperature=0.8,
                           system_prompt: str = "You are a helpful AI assistant.", conversation_history=None):
    if conversation_history is None:
        conversation_history = []
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{'role': 'system', 'content': system_prompt}] +
        conversation_history +
        [{'role': 'user', 'content': prompt}],
        temperature=temperature,
        stream=True
    )
    for chunk in response:
        chunk_message = chunk['choices'][0]['delta']
        text = chunk_message.get('content', '')
        yield text


def get_full_response(prompt, print_stream=True):
    collected_messages = []
    for chunk in stream_chat_completion(prompt):
        collected_messages.append(chunk)
        if print_stream:
            print(chunk, end='')
    full_reply_content = ''.join(collected_messages)
    return full_reply_content


# Demo
if __name__ == '__main__':
    test_prompt = "write a story about a cat that floods the house accidentally while its owners are on vacation"
    print("Prompt:", test_prompt)
    # stream the response
    print("Streaming the response:")
    get_full_response(test_prompt, print_stream=True)
    test_prompt_2 = "write a story about a horse that floods the house accidentally while its owners are on vacation"
    print("Prompt:", test_prompt_2)
    # wait for the response
    print("Waiting for the full response:")
    full_response = get_full_response(test_prompt_2, print_stream=False)
    print(full_response)

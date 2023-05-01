import openai

with open('apikey.txt', 'r') as f:
    API_KEY = f.read().strip()

openai.api_key = API_KEY


def stream_chat_completion(prompt, model='gpt-3.5-turbo', temperature=0.8):
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {'role': 'user', 'content': prompt}
        ],
        temperature=temperature,
        stream=True
    )

    for chunk in response:
        chunk_message = chunk['choices'][0]['delta']
        yield chunk_message.get('content', '')


def get_full_response(prompt, print_stream=True):
    collected_messages = []

    for chunk in stream_chat_completion(prompt):
        collected_messages.append(chunk)
        if print_stream:
            print(chunk, end='')

    full_reply_content = ''.join([m for m in collected_messages])
    return full_reply_content


if __name__ == '__main__':
    test_prompt = "write a story about a cat that floods the house accidentally while its owners are on vacation"
    full_response = get_full_response(test_prompt)
    print(f"Full conversation received: {full_response}")

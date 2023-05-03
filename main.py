import openai

with open('apikey.txt', 'r') as f:
    API_KEY = f.read().strip()

openai.api_key = API_KEY

TOKEN_LIMIT = 4097
CHARS_PER_TOKEN = 4  # approximate

conversation_history = []


def count_tokens(messages):
    counter = 0.0
    for message in messages:
        counter += len(message) / CHARS_PER_TOKEN
    return int(round(counter))


def stream_chat_completion(prompt: str, model: str = 'gpt-3.5-turbo', temperature=0.8,
                           system_prompt: str = "You are a helpful AI assistant."):
    global conversation_history

    messages = [{'role': 'system', 'content': system_prompt}] + \
        conversation_history + \
        [{'role': 'user', 'content': prompt}]

    if count_tokens(messages) >= TOKEN_LIMIT:
        # Summarize the conversation
        sum_messages = conversation_history + \
            [{'role': 'user', 'content': 'Summarize the entire above conversation'}]
        if count_tokens(sum_messages) < TOKEN_LIMIT:
            response = openai.ChatCompletion.create(
                model=model,
                messages=conversation_history,
                temperature=temperature,
            )
            conversation_history = [{'role': 'assistant', 'content': response.choices[0].message.content}]
        else:
            # as a last resort
            while count_tokens(messages) >= TOKEN_LIMIT:
                messages = messages[1:]

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
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
    test_prompt = "write a story about a cat that floods the house accidentally while its owners are on vacation\n"
    print("Prompt:", test_prompt)
    # stream the response
    print("Streaming the response:")
    get_full_response(test_prompt, print_stream=True)
    test_prompt_2 = "write a story about a horse that floods the house accidentally while its owners are on vacation\n"
    print("\n\nPrompt:", test_prompt_2)
    # wait for the response
    print("Waiting for the full response:")
    full_response = get_full_response(test_prompt_2, print_stream=False)
    print(full_response)

# Note: See example.py for a simplified example that just demonstrates simple streamed output
import openai
import json

with open('apikey.txt', 'r') as f:
    API_KEY = f.read().strip()

openai.api_key = API_KEY

conversation_history = []

# Load previous conversations from a file
try:
    with open('conversations.json', 'r') as conv_file:
        conversation_history = json.load(conv_file)
except FileNotFoundError:
    pass


def save_conversations(filename):
    with open(filename, 'w') as conv_file:
        json.dump(conversation_history, conv_file, indent=4)


def stream_chat_completion(prompt: str, model: str = 'gpt-3.5-turbo', temperature=0.8,
                           system_prompt: str = "You are a helpful AI assistant.", filename='conversations.json'):
    global conversation_history

    full_message = ""

    while True:
        messages = [{'role': 'system', 'content': system_prompt}] + \
                   conversation_history + \
                   [{'role': 'user', 'content': prompt}]
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=True
            )
            break
        except openai.error.InvalidRequestError:
            # truncate conversation
            conversation_history = conversation_history[1:]

    for chunk in response:
        chunk_message = chunk['choices'][0]['delta']
        text = chunk_message.get('content', '')
        full_message += text
        yield text

    # Save conversation history
    conversation_history.extend([
        {'role': 'user', 'content': prompt},
        {'role': 'assistant', 'content': full_message}
    ])
    save_conversations(filename)


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
    while True:
        prompt = input("Prompt: ")
        get_full_response(prompt, print_stream=True)
        print()

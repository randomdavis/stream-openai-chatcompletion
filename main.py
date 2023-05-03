import openai

with open('apikey.txt', 'r') as f:
    API_KEY = f.read().strip()

openai.api_key = API_KEY

TOKEN_LIMIT = 4097
CHARS_PER_TOKEN = 4  # approximate


class StreamingChatbot:
    def __init__(self):
        self.conversation_history = []

    def stream_chat_completion(self, prompt: str, model: str = 'gpt-3.5-turbo', temperature=0.8,
                               system_prompt: str = "You are a helpful AI assistant."):
        full_message = ""

        messages = [{'role': 'system', 'content': system_prompt}] + \
            self.conversation_history + \
            [{'role': 'user', 'content': prompt}]
        ensure_within_token_limit(messages)

        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True
        )

        for chunk in response:
            chunk_message = chunk['choices'][0]['delta']
            text = chunk_message.get('content', '')
            full_message += text
            yield text

        self.conversation_history.extend([
            {'role': 'user', 'content': prompt},
            {'role': 'assistant', 'content': full_message}
        ])

    def get_full_response(self, prompt, print_stream=True):
        collected_messages = []
        for chunk in self.stream_chat_completion(prompt):
            collected_messages.append(chunk)
            if print_stream:
                print(chunk, end='')
        full_reply_content = ''.join(collected_messages)
        return full_reply_content


def count_tokens(messages):
    counter = 0.0
    for message in messages:
        counter += len(message) / CHARS_PER_TOKEN
    return int(round(counter))


def summarize(message, model='gpt-3.5-turbo'):
    messages = [{"role": "user", "content": f"Please summarize the following message in a sentence: \"{message}\""}]

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages
    )
    summary = response['choices'][0]['message']['content']
    return summary


def ensure_within_token_limit(messages):
    while count_tokens(messages) >= TOKEN_LIMIT:
        message_to_remove = messages.pop(0)
        summary = summarize(message_to_remove['content'])
        messages.insert(0, {'role': message_to_remove['role'], 'content': summary})


# Demo
if __name__ == '__main__':
    bot = StreamingChatbot()
    while True:
        prompt = input("Prompt: ")
        bot.get_full_response(prompt, print_stream=True)
        print()

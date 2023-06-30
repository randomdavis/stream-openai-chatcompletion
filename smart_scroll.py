from tiktoken import Tokenizer, TokenList
import openai


class RelevanceBot:

    def __init__(self, api_key, model_name):
        self.system_message = "You are a helpful assistant that evaluates relevance."
        self.function_name = "evaluate_relevance"
        self.api_key = api_key
        self.model_name = model_name

    def is_relevant_chunk(self, chunk, query):
        function = {
            "name": self.function_name,
            "parameters": {
                "text": {"type": "string", "description": "The chunk of text to evaluate"},
                "query": {"type": "string", "description": "The query against which to evaluate the text"}
            },
            "output": {
                "type": "boolean",
                "description": "True if the text is relevant to the query, otherwise False"
            }
        }

        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": query},
            {"role": "assistant", "content": chunk},
        ]

        try:
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=messages,
                function_call=function,
            )
            if 'function_call' in response and 'outputs' in response['function_call']:
                if 'is_relevant' in response['function_call']['outputs']:
                    return response['function_call']['outputs']['is_relevant']
                else:
                    print("Key 'is_relevant' was not found in the function_call outputs")
                    return False
            else:
                print("Key 'function_call' or 'outputs' was not found in the response")
                return False
        except Exception as e:
            print(f"Error occurred when attempting to call the OpenAI API: {e}")
            return False


class SmartScroll:

    def __init__(self, text, query, window_size, api_key, model_name, token_limit):
        self.tokenizer = Tokenizer()
        self.text = text
        self.query = query
        self.window_size = window_size
        self.token_limit = token_limit

        # Create the RelevanceBot object
        self.relevance_bot = RelevanceBot(api_key, model_name)

        self.query_tokens = len(TokenList(self.tokenizer, self.query))

        # Calculate tokens used by the system message, query, and function call
        self.extra_tokens = len(TokenList(self.tokenizer, self.relevance_bot.system_message)) + \
                            self.query_tokens + \
                            len(TokenList(self.tokenizer,
                                          f'{self.relevance_bot.function_name}({{"text": "", "query": ""}})'))

    def text_to_chunks(self):
        tokens = list(self.tokenizer.tokenize(self.text))
        chunks = []

        for i in range(0, len(tokens), self.window_size):
            chunk_tokens = tokens[i:i + self.window_size]
            if len(chunk_tokens) + self.query_tokens + self.extra_tokens < self.token_limit * 0.85:
                chunk_text = ''.join(token.string for token in chunk_tokens)
                chunks.append(chunk_text)

        return chunks

    def __iter__(self):
        if not self.text.strip():
            return iter([])

        chunks_list = self.text_to_chunks()
        for chunk in chunks_list:
            if self.relevance_bot.is_relevant_chunk(chunk, self.query):
                yield chunk

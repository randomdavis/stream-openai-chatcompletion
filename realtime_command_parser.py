import asyncio
import openai
from gtts import gTTS
from playsound import playsound
import os
import tempfile
import subprocess

TOKEN_LIMIT = 4096
CHARS_PER_TOKEN = 4  # approximate


class Command:
    def __init__(self, cmd_str):
        self.cmd_str = cmd_str

    async def execute(self, command_executor):
        try:
            cmd, args_str = self.cmd_str.split('(', 1)
            args = args_str.rstrip(')').split(',')
            if cmd == "speak":
                await command_executor.speak(args[0].strip('"'))
            elif cmd == "wait":
                await command_executor.wait(float(args[0]))
            elif cmd == "run_python":
                await command_executor.run_python(args[0].strip('"'))
            elif cmd == "run_shell":
                await command_executor.run_shell(args[0].strip('"'))
        except Exception as e:
            print(f"[error] {e} [command] {self.cmd_str}")


class CommandExecutor:
    async def handle_tts_queue(self):
        while True:
            file_path = await self.tts_queue.get()
            if file_path is None:
                break
            await play_audio(file_path)
            os.remove(file_path)

    def reset_state(self):
        if self.handle_tts_task is not None:
            asyncio.ensure_future(self.handle_tts_task)

        self.tts_queue = asyncio.Queue()
        self.handle_tts_task = asyncio.create_task(self.handle_tts_queue())

    def __init__(self):
        self.tts_queue = asyncio.Queue()
        self.handle_tts_task = None
        self.reset_state()

    async def speak(self, text_to_speak):
        print(f"[speak] [{text_to_speak}]")
        tts = gTTS(text=text_to_speak, lang='en')
        file_path = os.path.join(tempfile.gettempdir(), f"tts_{hash(text_to_speak)}.mp3")
        tts.save(file_path)
        await self.tts_queue.put(file_path)

    async def wait(self, seconds):
        print(f"[wait] [{seconds}]")
        await asyncio.sleep(seconds)

    async def run_python(self, code):
        print(f"[run_python] [{code}]")
        output = subprocess.getoutput(f"python -c '{code}'")
        return output

    async def run_shell(self, command):
        print(f"[run_shell] [{command}]")
        output = subprocess.getoutput(command)
        return output


class ChatCompletion:
    main_system_prompt = """
        You are an AI connected to a Windows 10 PC. 
        You can run one or more commands when asked.
        Translate the user's natural language to commands.

        Commands include: 
        1. speak(text_to_speak) (NON-BLOCKING CALL)
        2. wait(seconds) (BLOCKING CALL)
        3. run_python(python_code) (BLOCKING CALL)
        4. run_shell(shell_command) (BLOCKING CALL)

        Example input:
        Speak a poem about robots and then wait for 5 seconds.
        Example output:
        speak("Robots work hard all day. Making life much easier. For us humans too");wait(5)

        Example input:
        Run a python script that prints 'Hello, World!'
        Example output:
        run_python("print('Hello, World!')")

        Example input:
        Run a shell command that prints the current directory.
        Example output:
        run_shell("dir")
        """

    def __init__(self, api_key, command_executor):
        self.api_key = api_key
        self.command_executor = command_executor
        self.conversation_history = [{'role': 'system', 'content': self.main_system_prompt}]
        openai.api_key = self.api_key

    def get_generator(self, prompt: str, model: str = 'gpt-3.5-turbo', temperature: float = 0.8):
        self.conversation_history += [{'role': 'user', 'content': prompt}]
        ensure_within_token_limit(self.conversation_history)

        generator = openai.ChatCompletion.create(
            model=model,
            messages=self.conversation_history,
            temperature=temperature,
            stream=True
        )
        return generator

    async def read_and_enqueue_commands(self, prompt, queue, print_text=False):
        generator = self.get_generator(prompt)

        while True:
            chunk = await get_chunk(generator)
            if chunk is None:
                break

            chunk_message = chunk['choices'][0]['delta']
            text = chunk_message.get('content', '')
            if print_text:
                print(text, end='')  # Print the text as it comes in
            await queue.put(text)

        await queue.put(None)  # Add sentinel value to indicate the end of the stream

    async def execute_commands(self, queue):
        command_text = ""
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            command_text += chunk
            if ';' in command_text:
                commands, remainder = command_text.rsplit(';', 1)
                command_list = commands.split(';')
                for cmd_str in command_list:
                    command = Command(cmd_str)
                    output = await command.execute(self.command_executor)
                    if output:
                        self.conversation_history.append({'role': 'assistant', 'content': output})
                        ensure_within_token_limit(self.conversation_history)
                command_text = remainder

        # Execute the remaining commands after the end of the stream
        command_list = command_text.split(';')
        for cmd_str in command_list:
            command = Command(cmd_str)
            output = await command.execute(self.command_executor)
            if output:
                self.conversation_history.append({'role': 'assistant', 'content': output})
                ensure_within_token_limit(self.conversation_history)


class PromptController:
    def __init__(self, api_key, command_executor=None):
        if command_executor is None:
            self.command_executor = CommandExecutor()
        else:
            self.command_executor = command_executor
        self.chat_completion = ChatCompletion(api_key, self.command_executor)

    async def handle_prompt(self, prompt):
        queue = asyncio.Queue()  # Clear the queue by creating a new instance
        self.command_executor.reset_state()  # Reset the state of the command executor

        read_task = asyncio.create_task(self.chat_completion.read_and_enqueue_commands(prompt, queue, print_text=True))
        execute_task = asyncio.create_task(self.chat_completion.execute_commands(queue))

        await asyncio.gather(read_task, execute_task)


def ensure_within_token_limit(conversation_history):
    total_tokens = sum([len(m['content']) // CHARS_PER_TOKEN for m in conversation_history])
    if total_tokens > TOKEN_LIMIT:
        overage = total_tokens - TOKEN_LIMIT
        while overage > 0:
            overage += len(conversation_history[0]['content']) // CHARS_PER_TOKEN
            del conversation_history[0]
        print("[warning] Had to remove some conversation history because we were over the token limit.")


async def get_chunk(generator):
    try:
        chunk = next(generator)
        return chunk
    except StopIteration:
        return None


async def play_audio(file_path):
    playsound(file_path)


async def main():
    command_executor = CommandExecutor()
    with open('apikey.txt', 'r') as f:
        api_key = f.read().strip()
    controller = PromptController(api_key, command_executor)

    while True:
        prompt = input("Enter prompt: ")
        await controller.handle_prompt(prompt)

if __name__ == "__main__":
    asyncio.run(main())

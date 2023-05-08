import asyncio
import openai
# import bot


# Stubbed bot functions that mimic the real ones but do nothing
async def move(distance):
    await asyncio.sleep(1)
    print(f"[move] [{distance}]")


async def speak(text_to_speak):
    await asyncio.sleep(1)
    print(f"[speak] [{text_to_speak}]")


async def turn(degrees):
    await asyncio.sleep(1)
    print(f"[turn] [{degrees}]")


async def wait(seconds):
    await asyncio.sleep(seconds)
    print(f"[wait] [{seconds}]")


with open('apikey.txt', 'r') as f:
    API_KEY = f.read().strip()

openai.api_key = API_KEY

main_system_prompt: str = """
You are an AI connected to a Robot. 
You can run one or more commands when asked.
Translate the user's natural language to commands.

Your messages are in the format:
command_1(argument_1_1,...,argument_1_n);command_2(argument_2_1,...,argument_2_n);command_m(argument_m_1,...,argument_m_n)

Commands are separated by ';', arguments are separated by ','. Don't split on anything inside double quotes because that's a string arugument.

Commands include: 
1. [move] [distance (in cm, positive or negative)] (BLOCKING CALL)
2. [speak] [text_to_speak] (NON-BLOCKING CALL)
3. [turn] [degrees] (BLOCKING CALL)
4. [wait] [seconds] (BLOCKING CALL)

Example input: Draw a 10cm x 10cm square while saying a haiku about robots.
Example output: speak("Robots work hard all day. Making life much easier. For us humans too");move(10.0);turn(90.0);move(10.0);turn(90.0);move(10.0);turn(90.0);move(10.0);speak(done!)
"""


def get_generator(prompt: str, model: str = 'gpt-3.5-turbo', temperature: float = 0.8,
                  system_prompt: str = main_system_prompt):
    messages = [{'role': 'system', 'content': system_prompt}] + \
               [{'role': 'user', 'content': prompt}]

    generator = openai.ChatCompletion.create(  # returns a generator when stream=True
        model=model,
        messages=messages,
        temperature=temperature,
        stream=True
    )
    return generator


async def get_chunk(generator):
    try:
        chunk = next(generator)
    except StopIteration:
        return None
    await asyncio.sleep(0)  # Yield control to the event loop
    return chunk


def stream_chat_completion(prompt: str, model: str = 'gpt-3.5-turbo', temperature: float = 0.8,
                           system_prompt: str = main_system_prompt):
    generator = get_generator(prompt, model, temperature, system_prompt)

    for chunk in generator:
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


def parse_commands(text: str):
    commands = []
    command = ""
    in_quotes = False
    for char in text:
        if char == '"' and not in_quotes:
            in_quotes = True
        elif char == '"' and in_quotes:
            in_quotes = False
        elif char == ';' and not in_quotes:
            commands.append(command.strip())
            command = ""
        else:
            command += char
    if command:
        commands.append(command.strip())
    return commands


async def execute_command_list(command_list):
    for cmd_str in command_list:
        try:
            cmd, args_str = cmd_str.split('(', 1)
            args = args_str.rstrip(')').split(',')
            if cmd == "move":
                await move(float(args[0]))
            elif cmd == "speak":
                await speak(args[0].strip('"'))
            elif cmd == "turn":
                await turn(float(args[0]))
            elif cmd == "wait":
                await wait(float(args[0]))
        except Exception as e:
            print(f"[error] {e}")


async def execute_commands(queue):
    command_text = ""
    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        command_text += chunk
        if ';' in command_text:
            commands, remainder = command_text.rsplit(';', 1)
            command_list = parse_commands(commands)
            await execute_command_list(command_list)
            command_text = remainder

    # Execute the remaining commands after the end of the stream
    command_list = parse_commands(command_text)
    await execute_command_list(command_list)


async def read_and_enqueue_commands(prompt, queue, print_text=False):
    generator = get_generator(prompt)

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


async def main():
    while True:
        prompt = input("Enter prompt: ")
        queue = asyncio.Queue()  # Clear the queue by creating a new instance
        task1 = asyncio.create_task(read_and_enqueue_commands(prompt, queue))
        task2 = asyncio.create_task(execute_commands(queue))
        await asyncio.gather(task1, task2)


if __name__ == "__main__":
    asyncio.run(main())

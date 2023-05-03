import threading
from queue import Queue
import subprocess
import requests
from bs4 import BeautifulSoup

from main import StreamingChatbot


def execute_python_code(code):
    try:
        output = eval(code)
        return str(output)
    except Exception as e:
        return str(e)


def perform_internet_search(query):
    search_url = f"https://www.google.com/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
    }
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    search_results = []

    for g in soup.find_all("div", class_="tF2Cxc"):
        title = g.find("h3", class_="LC20lb DKV0Md").text
        link = g.find("a")["href"]
        search_results.append({"title": title, "link": link})

    return search_results


def execute_console_command(command):
    try:
        output = subprocess.check_output(command, shell=True, text=True)
        return output.strip()
    except Exception as e:
        return str(e)


class AIAgent:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.chatbot = StreamingChatbot()

    def send_message(self, message):
        user_prompt = f"As {self.role}, respond to the following message: '{message}'"
        return self.chatbot.get_full_response(user_prompt)


class AdversarialAGI:
    def __init__(self):
        self.agent1 = AIAgent("Agent1", "Proponent")
        self.agent2 = AIAgent("Agent2", "Skeptic")
        self.queue1 = Queue()
        self.queue2 = Queue()

    def agent_communicate(self, agent, other_agent, message_queue, other_message_queue):
        while True:
            message = message_queue.get()
            if message == "quit":
                break

            # Parse command format and execute corresponding functions
            if message.startswith("py:"):
                code = message[3:]
                response = agent.execute_python_code(code)
            elif message.startswith("cmd:"):
                command = message[4:]
                response = agent.execute_console_command(command)
            elif message.startswith("search:"):
                query = message[7:]
                response = agent.perform_internet_search(query)
            else:
                response = agent.send_message(message)

            other_message_queue.put(response)

    def run(self):
        t1 = threading.Thread(target=self.agent_communicate, args=(self.agent1, self.agent2, self.queue1, self.queue2))
        t2 = threading.Thread(target=self.agent_communicate, args=(self.agent2, self.agent1, self.queue2, self.queue1))

        t1.start()
        t2.start()

        system_prompt = (
            "You are a helpful AI assistant. Agent1, you are the Proponent, and Agent2, you are the Skeptic. "
            f"The user wants you to do the following: {input('What do you want the AI to do? ')} "
            "You can use the following commands to execute Python code (py:CODE), "
            "run console commands (cmd:COMMAND), and perform internet searches (search:QUERY).")

        self.queue1.put(system_prompt)

        while True:
            try:
                message = self.queue2.get(timeout=60)
                if message == "quit":
                    break
                print(f"{self.agent2.name}: {message}")
            except Exception as e:
                print("No response received, terminating the conversation.")
                self.queue1.put("quit")
                break

        t1.join()
        t2.join()


# Initialization and execution of the Adversarial AGI system
if __name__ == '__main__':
    agi = AdversarialAGI()
    agi.run()

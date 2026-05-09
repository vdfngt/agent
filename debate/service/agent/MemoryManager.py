
from langchain_core.messages.base import BaseMessage
from langchain.messages import SystemMessage,HumanMessage,AIMessage

class MessageContent:
    name: str
    text: str
    message: BaseMessage

    def __init__(self, name: str, text: str,role: str):
        self.text = text
        self.name = name
        if role == "assistant":
            self.message = AIMessage(role=role, content=f"[{name}]:{text}")
        else:
            self.message = HumanMessage(role=role, content=f"[{name}]:{text}")


class MemoryManager:
    messages: list[MessageContent] = []

    def append(self, message: MessageContent):
        self.messages.append(message)

    def write(self, filename: str):
        with open(filename, "w") as f:
            for message in self.messages:
                f.write(f"{message.name}: {message.text}\n")

    def clear(self):
        self.messages = []
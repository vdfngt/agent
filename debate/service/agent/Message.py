import json
import re
from langchain_core.messages.base import BaseMessage
from langchain.messages import SystemMessage,HumanMessage,AIMessage
class Message:

    def __init__(self, message: BaseMessage):
        self.message = message
        json_str = message.content
        self.name = re.findall(r'<name>(.*?)</name>', json_str)[0]
        self.text = re.findall(r'<text>(.*?)</text>', json_str, re.DOTALL)[0]
        self.point = re.findall(r'<point>(.*?)</point>', json_str)[0]

    def aiMessage(self):
        return AIMessage(content=f"[{self.name}]: {self.text}")

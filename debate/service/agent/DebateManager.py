import asyncio
from time import sleep

from fastapi import Request

from agent.MemoryManager import MemoryManager, MessageContent
from agent.Role import Role
from config import Settings
from langchain.messages import SystemMessage,HumanMessage,AIMessage
from langchain_core.messages.base import BaseMessage
import logging

from model.model import RunRequest



class DebateManager:
    judge: Role = None
    debater_roles: list[Role] = []

    memory_manager = MemoryManager()

    def __init__(self, config: Settings):
        self.judge = Role(config.judge_role)
        self.debater_roles = [Role(role) for role in config.debater_roles]

    def listMessages(self):
        return [message.message for message in self.memory_manager.messages]

    def streaming(self, param: RunRequest):
        debater = self.getDebaterRolesByName(param.to_name)
        for text in param.text:
            self.memory_manager.append(MessageContent(name=param.from_name, text=text, role="human"))
        return debater.streaming(self.listMessages())
            

    # def run(self, input: str):
    #     # 立论环节
    #     print("立论环节")
    #     self.messages.append(HumanMessage(content=input))
    #     for debater in self.debater_roles:
    #         print(f"--{debater.name}：--")
    #         self.messages.append(AIMessage(role="assistant", content=f"[{self.judge.name}]:请{debater.name}发表自己的观点,至少500字。"))
    #         print(f"{self.judge.name}：{self.messages[-1].content}")
    #         content = debater.run(self.messages)
    #         if content is None:
    #             continue
    #         self.messages.append(content.aiMessage())
    #         print(f"{debater.name}：{content.text}")
            
    #     # 辩论环节
    #     print("辩论环节")
    #     for debater in self.debater_roles:
    #         self.messages.append(AIMessage(role="assistant", content=f"请{debater.name}选择一个辩论者的观点进行质询"))
    #         print(f"{self.judge.name}：{self.messages[-1].content}")
    #         content = debater.run(self.messages)
    #         self.messages.append(content.aiMessage())
    #         print(f"{debater.name}：{content.text}")


    #         nexter = self.getDebaterRolesByName(content.point)
    #         print(f"{self.judge.name}：{nexter.name}")
    #         self.messages.append(AIMessage(role="assistant", content=f"请回答{debater.name}的质询"))
    #         print(f"{self.judge.name}：{self.messages[-1].content}")
    #         content = nexter.run(self.messages)
    #         self.messages.append(content.aiMessage())
    #         print(f"{nexter.name}：{content.text}")
    #     # # 结果环节
    #     # print("结果环节")
    #     # for debater in self.debater_roles:
    #     #     self.messages.append({"role": "assistant", "content": f"请{debater.name}投票，选择除你以外的辩论者，输出他的名字"})
    #     #     content = debater.run({"messages": self.messages})
    #     #     self.messages.append({"role": "assistant", "content": content["content"]})
    #     # # 统计结果
    #     # print("统计结果")

    #     # self.messages.append({"role": "assistant", "content": "请统计投票结果"})
    #     # content = self.judge.run({"messages": self.messages})
    #     # self.messages.append({"role": "assistant", "content": content})
    #     return self.messages
    
    def getDebaterRolesByName(self, name: str):
        if self.judge.name == name:
            return self.judge
        for debater in self.debater_roles:
            if debater.name == name:
                return debater
    
    def listDebaterRoles(self):
        return {
            "judge": self.judge.name,
            "debater": [debater.name for debater in self.debater_roles]
        }
from langchain.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate,PromptTemplate
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
import os
from .Message import Message
class Role:
    def __init__(self, role: dict,):
        self.role = role["role"]
        self.name = role["name"]
        self.prompt_file = role["prompt_file"]
        self.system_prompt = PromptTemplate.from_file(self.prompt_file,encoding="utf-8").template
        self.llm = ChatOpenAI(
            temperature=1,
            model=os.getenv("openai_model"),
            openai_api_key=os.getenv("openai_api_key"),
            openai_api_base=os.getenv("openai_base_url"),
            streaming=True,
        )
        self.agent = create_agent(
            tools=[],
            model=self.llm,
            system_prompt=self.system_prompt,
        )
    
    def run(self, messages: list):
      
      req = self.agent.invoke({"messages": messages})
      if req["messages"][-1].content == "":
        return None
      return Message(req["messages"][-1])


    def streaming(self, messages: list):
        return self.agent.stream({"messages": messages},stream_mode="messages")

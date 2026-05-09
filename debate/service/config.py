from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    app_name: str = "辩论agent"
    app_description: str = "一个用于展示辩论agent的FastAPI应用"
    app_version: str = "1.0.0"

    openai_api_key: str = "xxxxxxxx"
    openai_base_url: str = "https://open.bigmodel.cn/api/paas/v4/"
    openai_model: str = "glm-4-flash"
    judge_role: dict = {
        "name": "裁判",
        "role": "judge",
        "description": "你是一个专业的辩论裁判，负责判断辩论结果。",
        "prompt_file": "prompts/judge_prompt.txt",
    }
    debater_roles: List[dict] = [
        {
            "name": "小儒",
            "role": "debater",
            "description": "你是一个专业的小儒，负责与用户进行分析辩论。",
            "prompt_file": "prompts/small_rug_prompt.txt",
        },
        {
            "name": "小道",
            "role": "debater",
            "description": "你是一个专业的小道，负责与用户进行分析辩论。",
            "prompt_file": "prompts/small_way_prompt.txt",
        },
        {
            "name": "小佛",
            "role": "debater",
            "description": "你是一个专业的小佛，负责与用户进行分析辩论。",
            "prompt_file": "prompts/small_fool_prompt.txt",
        },
        {
            "name": "小马",
            "role": "debater",
            "description": "你是一个专业的小马，负责与用户进行分析辩论。",
            "prompt_file": "prompts/small_mouse_prompt.txt",
        },
    ]


from pydantic import BaseModel


class RunRequest(BaseModel):
    from_name: str
    to_name: str
    text: list[str]
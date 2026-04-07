from pydantic import BaseModel


class Config(BaseModel):
    GROUP_NAME_PREFIX: str = "Untitled Story"
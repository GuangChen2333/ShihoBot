from pydantic import BaseModel


class Config(BaseModel):
    WEBHOOK_PATH: str = "/webhook/send"
    WEBHOOK_GROUP_ID: int | None = None
    WEBHOOK_SECRET: str | None = None

from pydantic import BaseModel


class Config(BaseModel):
    LLM_ONLY_ON_AT: bool = False
    LLM_POKE_SLEEP_TIME: int = 5
    LLM_POKE_INTERVAL: float = 0.5

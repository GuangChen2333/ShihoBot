from pydantic import BaseModel


class Config(BaseModel):
    LLM_CONTINUITIER_BASE_URL: str
    LLM_CONTINUITIER_API_KEY: str
    LLM_CONTINUITIER_MODEL: str = "gpt-5-nano"
    LLM_CONTINUITIER_PROMPT: str = """
请判断群聊中最后一条消息是否开启了新话题，或与之前的消息无关。以下是判断标准：
1. **新话题**：该消息与群聊中的历史消息没有直接关联，转向了一个独立的新话题。
2. **延续性话题**：该消息与之前的消息内容相关，是对话的自然延续。
3. **重复信息**：如果该消息与之前的某条消息完全或几乎完全相同，视为重复信息，不算新话题。

根据这些标准，请返回：
- "true" 表示新话题
- "false" 表示延续性话题或重复信息

请根据上下文和消息内容做出判断，结果只包含 "true" 或 "false"。
"""

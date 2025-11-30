from typing import List

from openai.types.chat import ChatCompletionUserMessageParam, ChatCompletionAssistantMessageParam


class StringContext:
    def __init__(self, max_context_count: int):
        self._max_context_count = max_context_count
        self._messages = []

    @property
    def messages(self) -> List[str]:
        return self._messages.copy()

    def push(self, msg: str) -> None:
        self._messages.append(msg)
        if len(self._messages) > self._max_context_count:
            self._messages.pop(0)

    def build(self) -> str:
        return "\n".join(self._messages)


class ChatCompletionContext:
    def __init__(self, max_context_count: int):
        self._max_context_count = max_context_count
        self._messages = []

    @property
    def messages(self) -> List[ChatCompletionUserMessageParam | ChatCompletionAssistantMessageParam]:
        return self._messages.copy()

    def push(self, completion: ChatCompletionUserMessageParam | ChatCompletionAssistantMessageParam) -> None:
        self._messages.append(completion)
        if len(self._messages) > self._max_context_count:
            self._messages.pop(0)

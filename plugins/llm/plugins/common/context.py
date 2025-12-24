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
        self._user_msgs = []

    @property
    def messages(self) -> List[ChatCompletionUserMessageParam | ChatCompletionAssistantMessageParam]:
        if len(self._user_msgs) > 0:
            self._push(
                ChatCompletionUserMessageParam(
                    role="user",
                    content='\n'.join(self._user_msgs),
                )
            )
            self._user_msgs.clear()

        return self._messages.copy()

    def _push(self, completion: ChatCompletionUserMessageParam | ChatCompletionAssistantMessageParam) -> None:
        self._messages.append(completion)
        if len(self._messages) > self._max_context_count:
            self._messages.pop(0)

    def push_user(self, nick_name: str, context: str) -> None:
        self._user_msgs.append(
            f"{nick_name}: {context}"
        )

    def push_assistant(self, context: str) -> None:
        self._push(
            ChatCompletionAssistantMessageParam(
                role="assistant",
                content=context
            ))

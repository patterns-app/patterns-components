from __future__ import annotations

import math
import re
from dataclasses import dataclass

from pydantic import BaseModel
from slack_sdk import WebClient


class Message(BaseModel):
    ts: float
    user: str
    text: str
    replies: list[Message]


@dataclass
class SlackClient:
    channel_id: str
    oldest_message_time: float
    users_by_id: dict[str, dict]
    client: WebClient

    def get_thread_messages(self, thread_ts: str) -> list[Message]:
        messages = []
        replies = self.client.conversations_replies(
            channel=self.channel_id,
            ts=thread_ts,
            oldest=math.floor(self.oldest_message_time),
            limit=100,
            cursor=None
        )
        replies.validate()
        for m in replies.get('messages', [None])[1:]:
            messages.append(self.message_from_dict(m))
    
        return messages

    def get_channel_messages(self) -> list[Message]:
        messages = []
        next_cursor = None
        while True:
            history = self.client.conversations_history(
                channel=self.channel_id, 
                oldest=math.floor(self.oldest_message_time),
                limit=100,
                cursor=next_cursor
            )
            history.validate()

            for m_dict in history.get("messages", []):
                m = self.message_from_dict(m_dict)
                if thread_ts := m_dict.get('thread_ts'):
                    m.replies = self.get_thread_messages(thread_ts)

                messages.append(m)

            next_cursor = history.get("response_metadata", {}).get("next_cursor", '')
            if not next_cursor:
                break
        return messages

    def message_from_dict(self, d: dict) -> Message:
        user = d.get('user')        
        if real_user := self.users_by_id.get(user):
            user = real_user["real_name"]

        text = d.get('text', '')
        for f in re.findall(r"<@(U[A-Z0-9]+)>", text):
            if real_user := self.users_by_id.get(f):
                text = text.replace(f"<@{f}>", real_user["real_name"])

        if d.get("subtype") == "bot_message":
            user = f"🤖Bot"

        return Message(
            ts=float(d.get('ts')),
            user=user,
            text=text,
            replies=[]
        )


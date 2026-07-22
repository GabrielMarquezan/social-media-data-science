from dataclasses import dataclass, field
from datetime import datetime

from social_media.src.domain.author import Author


@dataclass(frozen=True)
class Comment:
    id: str
    text: str
    owner: Author
    timestamp: datetime | None
    likes_count: int | None
    replies_count: int | None
    replies: list["Comment"] = field(default_factory=list)

from dataclasses import dataclass
from datetime import datetime

from social_media.src.domain.author import Author
from social_media.src.domain.comment import Comment


@dataclass(frozen=True)
class Post:
    id: str
    type: str
    short_code: str
    caption: str | None
    hashtags: list[str]
    mentions: list[str]
    url: str
    comments_count: int | None
    first_comment: str | None
    latest_comments: list[Comment]
    likes_count: int | None
    timestamp: datetime | None
    owner: Author
    product_type: str | None
    views: int | None = None
    video_duration: float | None = None

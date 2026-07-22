from dataclasses import dataclass


@dataclass(frozen=True)
class Author:
    id: str | None
    username: str | None
    full_name: str | None
    is_verified: bool | None
    profile_pic_url: str | None

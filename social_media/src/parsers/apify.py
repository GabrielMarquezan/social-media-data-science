import logging
from datetime import datetime, timezone
from typing import Any

from social_media.src.domain.author import Author
from social_media.src.domain.comment import Comment
from social_media.src.domain.post import Post

logger = logging.getLogger(__name__)


def parse_apify_json(raw: list[dict[str, Any]]) -> list[Post]:
    """Converte uma lista de posts no formato Apify em uma lista de Posts de domínio."""
    posts: list[Post] = []
    for item in raw:
        try:
            post = _parse_post(item)
            posts.append(post)
        except Exception as exc:
            logger.exception(
                "Falha ao fazer parse de um post do Apify: %s",
                exc,
                extra={"post_id": item.get("id")},
            )
    return posts


def _parse_post(data: dict[str, Any]) -> Post:
    owner = _parse_post_owner(data)
    latest_comments = _parse_latest_comments(data.get("latestComments", []) or [])

    return Post(
        id=_require_str(data, "id"),
        type=_require_str(data, "type"),
        short_code=_require_str(data, "shortCode"),
        caption=_get_str(data, "caption"),
        hashtags=_get_list(data, "hashtags"),
        mentions=_get_list(data, "mentions"),
        url=_get_str(data, "url"),
        comments_count=_get_int(data, "commentsCount"),
        first_comment=_get_str(data, "firstComment"),
        latest_comments=latest_comments,
        likes_count=_get_int(data, "likesCount"),
        timestamp=_parse_datetime(data.get("timestamp")),
        owner=owner,
        product_type=_get_str(data, "productType"),
        views=_get_int(data, "videoViewCount"),
        video_duration=_get_float(data, "videoDuration"),
    )


def _parse_post_owner(data: dict[str, Any]) -> Author:
    if "owner" in data and isinstance(data["owner"], dict):
        return _parse_author(data["owner"])

    return Author(
        id=_get_str(data, "ownerId"),
        username=_get_str(data, "ownerUsername"),
        full_name=_get_str(data, "ownerFullName"),
        is_verified=None,
        profile_pic_url=None,
    )


def _parse_latest_comments(items: list[dict[str, Any]]) -> list[Comment]:
    comments: list[Comment] = []
    for item in items:
        try:
            comments.append(_parse_comment(item))
        except Exception as exc:
            logger.exception(
                "Falha ao fazer parse de um comentário: %s",
                exc,
                extra={"comment_id": item.get("id")},
            )
    return comments


def _parse_comment(data: dict[str, Any]) -> Comment:
    owner = _parse_author(data.get("owner")) if isinstance(data.get("owner"), dict) else _parse_comment_owner_fallback(data)

    replies = _parse_replies(data.get("replies") or [])

    return Comment(
        id=_require_str(data, "id"),
        text=_get_str(data, "text") or "",
        owner=owner,
        timestamp=_parse_datetime(data.get("timestamp")),
        likes_count=_get_int(data, "likesCount"),
        replies_count=_get_int(data, "repliesCount"),
        replies=replies,
    )


def _parse_replies(items: list[dict[str, Any]] | None) -> list[Comment]:
    if not items:
        return []
    replies: list[Comment] = []
    for item in items:
        try:
            replies.append(_parse_comment(item))
        except Exception as exc:
            logger.exception(
                "Falha ao fazer parse de uma resposta: %s",
                exc,
                extra={"reply_id": item.get("id")},
            )
    return replies


def _parse_comment_owner_fallback(data: dict[str, Any]) -> Author:
    return Author(
        id=None,
        username=_get_str(data, "ownerUsername"),
        full_name=None,
        is_verified=None,
        profile_pic_url=_get_str(data, "ownerProfilePicUrl"),
    )


def _parse_author(data: dict[str, Any]) -> Author:
    return Author(
        id=_get_str(data, "id"),
        username=_get_str(data, "username"),
        full_name=_get_str(data, "full_name"),
        is_verified=data.get("is_verified") if isinstance(data.get("is_verified"), bool) else None,
        profile_pic_url=_get_str(data, "profile_pic_url"),
    )


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (OSError, ValueError, OverflowError):
            return None
    return None


def _get_str(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _require_str(data: dict[str, Any], key: str) -> str:
    value = _get_str(data, key)
    if value is None:
        raise ValueError(f"Campo obrigatório ausente: {key}")
    return value


def _get_int(data: dict[str, Any], key: str) -> int | None:
    value = data.get(key)
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _get_float(data: dict[str, Any], key: str) -> float | None:
    value = data.get(key)
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _get_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key)
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]

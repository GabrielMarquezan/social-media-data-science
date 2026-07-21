import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd

from social_media.src.config import Config
from social_media.src.dependencies import Dependencies
from social_media.src.domain.comment import Comment
from social_media.src.domain.post import Post
from social_media.src.parsers.apify import parse_apify_json


def parse_step(
    dfs: dict[str, pd.DataFrame], config: Config, deps: Dependencies
) -> dict[str, pd.DataFrame]:
    """Lê o JSON bruto do Apify e popula os DataFrames `posts` e `comments`."""
    raw_json_path = dfs.get("raw_json_path")
    if raw_json_path is None:
        raise ValueError("raw_json_path não encontrado no dicionário de DataFrames.")

    path = Path(raw_json_path)
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    posts = parse_apify_json(raw)

    posts_df = _build_posts_df(posts)
    comments_df = _build_comments_df(posts)

    dfs = dict(dfs)
    dfs["posts"] = posts_df
    dfs["comments"] = comments_df
    return dfs


def _build_posts_df(posts: list[Post]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for post in posts:
        row = asdict(post)
        row.pop("latest_comments", None)
        row.update(_flatten_author(row.pop("owner", {})))
        rows.append(row)
    return pd.DataFrame(rows) if rows else _empty_posts_df()


def _build_comments_df(posts: list[Post]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for post in posts:
        for comment in post.latest_comments:
            rows.extend(_flatten_comment(comment, post.id))
    return pd.DataFrame(rows) if rows else _empty_comments_df()


def _flatten_comment(comment: Comment, post_id: str, parent_id: str | None = None, depth: int = 0) -> list[dict[str, Any]]:
    """Converte um comentário e suas respostas em linhas tabulares."""
    replies = comment.replies or []
    row = asdict(comment)
    row["post_id"] = post_id
    row["parent_id"] = parent_id
    row["depth"] = depth
    row.pop("replies", None)
    row.update(_flatten_author(row.pop("owner", {})))
    rows = [row]
    for reply in replies:
        rows.extend(_flatten_comment(reply, post_id, parent_id=comment.id, depth=depth + 1))
    return rows


def _flatten_author(author: dict[str, Any]) -> dict[str, Any]:
    return {
        "owner_id": author.get("id"),
        "owner_username": author.get("username"),
        "owner_full_name": author.get("full_name"),
        "owner_is_verified": author.get("is_verified"),
        "owner_profile_pic_url": author.get("profile_pic_url"),
    }


def _empty_posts_df() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "id",
            "type",
            "short_code",
            "caption",
            "hashtags",
            "mentions",
            "url",
            "comments_count",
            "first_comment",
            "likes_count",
            "timestamp",
            "product_type",
            "views",
            "video_duration",
            "owner_id",
            "owner_username",
            "owner_full_name",
            "owner_is_verified",
            "owner_profile_pic_url",
        ]
    )


def _empty_comments_df() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "id",
            "text",
            "timestamp",
            "likes_count",
            "replies_count",
            "post_id",
            "parent_id",
            "depth",
            "owner_id",
            "owner_username",
            "owner_full_name",
            "owner_is_verified",
            "owner_profile_pic_url",
        ]
    )

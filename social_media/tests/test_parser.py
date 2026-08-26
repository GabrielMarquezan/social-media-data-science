import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from social_media.src.domain.author import Author
from social_media.src.parsers.apify import parse_apify_json

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> list[dict]:
    with open(FIXTURES_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def test_parse_real_sample() -> None:
    raw = load_fixture("real_sample.json")
    posts = parse_apify_json(raw)

    assert len(posts) == 1
    post = posts[0]

    assert post.id == "3447591998317965502"
    assert post.type == "Sidecar"
    assert post.short_code == "C_YTqgGOLC-"
    assert post.caption == "slow down you crazy child 🪩"
    assert post.likes_count == 3
    assert post.comments_count == 24
    assert post.views is None
    assert post.video_duration is None
    assert len(post.latest_comments) == 15
    assert post.first_comment == "Perfeita, te amo!!❤️❤️❤️❤️"


def test_parse_synthetic_posts() -> None:
    raw = load_fixture("synthetic_posts.json")
    posts = parse_apify_json(raw)

    assert len(posts) == 3

    by_id = {post.id: post for post in posts}

    image = by_id["img_001"]
    assert image.type == "Image"
    assert image.views is None
    assert image.video_duration is None
    assert len(image.latest_comments) == 2
    assert image.latest_comments[1].replies_count == 1
    assert len(image.latest_comments[1].replies) == 1
    assert image.latest_comments[1].replies[0].text == "Uso o Lightroom."

    video = by_id["vid_001"]
    assert video.type == "Video"
    assert video.views == 1500
    assert video.video_duration == 15.5
    assert len(video.latest_comments) == 1

    sidecar = by_id["side_001"]
    assert sidecar.type == "Sidecar"
    assert sidecar.caption is None
    assert sidecar.latest_comments == []
    assert sidecar.views is None


def test_post_owner_from_flat_fields() -> None:
    raw = load_fixture("synthetic_posts.json")
    posts = parse_apify_json(raw)

    post = posts[0]
    assert post.owner == Author(
        id="u002",
        username="autor_post",
        full_name="Autor do Post",
        is_verified=None,
        profile_pic_url=None,
    )


def test_comment_owner_from_object() -> None:
    raw = load_fixture("synthetic_posts.json")
    posts = parse_apify_json(raw)

    comment = posts[0].latest_comments[0]
    assert comment.owner == Author(
        id="u001",
        username="comentador1",
        full_name="Comentador Um",
        is_verified=True,
        profile_pic_url="https://example.com/u001.jpg",
    )


def test_ignores_child_posts() -> None:
    raw = load_fixture("synthetic_posts.json")
    posts = parse_apify_json(raw)

    assert len(posts) == 3
    child_ids = [post.id for post in posts if post.id.startswith("child_")]
    assert child_ids == []


def test_tolerates_malformed_items() -> None:
    raw = [
        {"id": "valid_001", "type": "Image", "shortCode": "VALID001"},
        {"id": "invalid_001", "type": "Image"},
        {"type": "Image", "shortCode": "NO_ID"},
    ]
    posts = parse_apify_json(raw)

    assert len(posts) == 1
    assert posts[0].id == "valid_001"


def test_timestamp_parsing() -> None:
    raw = [
        {
            "id": "ts_001",
            "type": "Image",
            "shortCode": "TS001",
            "timestamp": "2024-01-15T10:00:00.000Z",
            "latestComments": [],
        }
    ]
    posts = parse_apify_json(raw)

    assert len(posts) == 1
    assert posts[0].timestamp == datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)


def test_optional_views_and_duration() -> None:
    raw = [
        {
            "id": "opt_001",
            "type": "Image",
            "shortCode": "OPT001",
            "latestComments": [],
        }
    ]
    posts = parse_apify_json(raw)

    assert len(posts) == 1
    assert posts[0].views is None
    assert posts[0].video_duration is None


def test_parse_reel_item() -> None:
    """Reels chegam do Apify como type=Video/productType=clips e devem parsear."""
    raw = [
        {
            "id": "reel_001",
            "type": "Video",
            "shortCode": "DEF456abc",
            "caption": "novo reel da coleção",
            "url": "https://www.instagram.com/reel/DEF456abc/",
            "commentsCount": 1,
            "likesCount": 150,
            "timestamp": "2025-01-10T18:30:00.000Z",
            "ownerUsername": "loja",
            "productType": "clips",
            "videoViewCount": 5000,
            "videoDuration": 12.5,
            "latestComments": [
                {
                    "id": "c1",
                    "text": "ameei esse reel",
                    "timestamp": "2025-01-10T19:00:00.000Z",
                    "ownerUsername": "fan1",
                }
            ],
        }
    ]
    posts = parse_apify_json(raw)

    assert len(posts) == 1
    reel = posts[0]
    assert reel.type == "Video"
    assert reel.product_type == "clips"
    assert reel.views == 5000
    assert reel.video_duration == 12.5
    assert len(reel.latest_comments) == 1
    assert reel.latest_comments[0].text == "ameei esse reel"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

import pandas as pd

from social_media.src.metrics.content_type import community_index, new_commenter_share


def test_community_index() -> None:
    posts = pd.DataFrame(
        {
            "id": ["p1", "p2", "p3", "p4"],
            "type": ["Image", "Image", "Video", "Video"],
        }
    )
    comments = pd.DataFrame(
        {
            "post_id": ["p1", "p1", "p2", "p2", "p3", "p3", "p4", "p4"],
            "owner_id": ["u1", "u2", "u1", "u2", "u1", "u3", "u1", "u3"],
        }
    )
    result = community_index(posts, comments)
    # Image: u1 e u2 comentaram em 2 posts cada -> 2 recorrentes / 2 únicos = 1.0
    assert result.loc["Image"] == 1.0
    # Video: u1 e u3 comentaram em 2 posts cada -> 2 recorrentes / 2 únicos = 1.0
    assert result.loc["Video"] == 1.0


def test_new_commenter_share() -> None:
    posts = pd.DataFrame(
        {
            "id": ["p1", "p2"],
            "type": ["Image", "Image"],
        }
    )
    comments = pd.DataFrame(
        {
            "post_id": ["p1", "p1", "p2", "p2"],
            "owner_id": ["u1", "u2", "u1", "u3"],
        }
    )
    result = new_commenter_share(posts, comments)
    # Image: u1 recorrente (2 posts), u2 e u3 novos (1 post cada)
    # total comentários = 4, novos = 2 (u2, u3) -> 0.5
    assert result.loc["Image"] == 0.5


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])

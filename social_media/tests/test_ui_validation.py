import pytest

from social_media.src.ui.validation import find_invalid_links, parse_links


@pytest.mark.parametrize(
    "url",
    [
        "https://www.instagram.com/p/ABC123/",
        "https://www.instagram.com/p/ABC123",
        "https://www.instagram.com/p/a-b_c09/",
        "https://www.instagram.com/p/ABC123/?img_index=1",
        "https://www.instagram.com/p/ABC123/#comments",
        "https://www.instagram.com/reel/ABC123/",
        "https://www.instagram.com/reel/ABC123",
        "https://www.instagram.com/reels/ABC123/",
        "https://www.instagram.com/reel/a-b_c09/?igsh=abc123",
    ],
)
def test_valid_instagram_urls(url: str) -> None:
    assert find_invalid_links([url]) == []


@pytest.mark.parametrize(
    "url",
    [
        "https://instagram.com/p/ABC123/",  # sem www
        "https://instagram.com/reel/ABC123/",  # sem www
        "http://www.instagram.com/p/ABC123/",  # sem https
        "https://www.instagram.com/tv/ABC123/",  # IGTV não suportado
        "https://www.instagram.com/stories/ABC123/",  # stories não suportados
        "https://www.instagram.com/p/",  # shortcode vazio
        "https://www.instagram.com/reel/",  # shortcode vazio
        "https://www.instagram.com/",
        "não-é-uma-url",
        "ftp://www.instagram.com/p/ABC123/",
    ],
)
def test_invalid_instagram_urls(url: str) -> None:
    assert find_invalid_links([url]) == [url]


def test_parse_links_strips_and_ignores_blank_lines() -> None:
    text = "  https://www.instagram.com/p/A/  \n\n\nhttps://www.instagram.com/p/B/\n   \n"
    assert parse_links(text) == [
        "https://www.instagram.com/p/A/",
        "https://www.instagram.com/p/B/",
    ]


def test_parse_links_empty_text() -> None:
    assert parse_links("") == []
    assert parse_links("   \n  \n") == []


def test_find_invalid_links_mixed() -> None:
    links = [
        "https://www.instagram.com/p/OK/",
        "https://instagram.com/p/SEM-WWW/",
    ]
    assert find_invalid_links(links) == ["https://instagram.com/p/SEM-WWW/"]

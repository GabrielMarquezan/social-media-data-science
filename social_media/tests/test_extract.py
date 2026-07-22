import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from social_media.src.config import build_config
from social_media.src.extract.apify import extract
from social_media.src.main import read_links


def test_read_links(tmp_path: Path) -> None:
    links_file = tmp_path / "links.txt"
    links_file.write_text("  https://instagram.com/p/A  \n\nhttps://instagram.com/p/B\n", encoding="utf-8")

    result = read_links(links_file)
    assert result == ["https://instagram.com/p/A", "https://instagram.com/p/B"]


def test_read_links_raises_when_missing() -> None:
    with pytest.raises(FileNotFoundError):
        read_links(Path("/caminho/que/nao/existe/links.txt"))


@pytest.mark.anyio
async def test_extract_saves_dataset(tmp_path: Path) -> None:
    config = build_config(
        apify_token="test-token",
        data_dir=tmp_path / "data",
    )
    run_id = "run-123"
    links = ["https://instagram.com/p/A"]

    mock_dataset_client = MagicMock()
    mock_dataset_client.list_items = AsyncMock(
        return_value=MagicMock(items=[{"id": "post_1"}])
    )

    mock_run_client = MagicMock()
    mock_run_client.dataset.return_value = mock_dataset_client

    mock_actor_client = MagicMock()
    mock_actor_client.call = AsyncMock(return_value=MagicMock())
    mock_actor_client.last_run.return_value = mock_run_client

    mock_apify_client = MagicMock()
    mock_apify_client.actor.return_value = mock_actor_client

    with patch(
        "social_media.src.extract.apify.ApifyClientAsync",
        return_value=mock_apify_client,
    ):
        result_path = await extract(links, config, run_id)

    assert result_path == config.data_dir / f"raw_{run_id}.json"
    assert result_path.exists()

    saved = json.loads(result_path.read_text(encoding="utf-8"))
    assert saved == [{"id": "post_1"}]

    mock_actor_client.call.assert_awaited_once()
    call_args = mock_actor_client.call.call_args.kwargs["run_input"]
    assert call_args["directUrls"] == links
    assert call_args["resultsType"] == "posts"
    assert "searchLimit" not in call_args
    assert "searchType" not in call_args


@pytest.mark.anyio
async def test_extract_raises_when_call_returns_none(tmp_path: Path) -> None:
    config = build_config(
        apify_token="test-token",
        data_dir=tmp_path / "data",
    )

    mock_actor_client = MagicMock()
    mock_actor_client.call = AsyncMock(return_value=None)

    mock_apify_client = MagicMock()
    mock_apify_client.actor.return_value = mock_actor_client

    with patch(
        "social_media.src.extract.apify.ApifyClientAsync",
        return_value=mock_apify_client,
    ):
        with pytest.raises(RuntimeError, match="Falha na chamada do ator Apify"):
            await extract(["https://instagram.com/p/A"], config, "run-123")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

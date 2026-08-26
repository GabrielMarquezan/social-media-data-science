import asyncio
import json
from pathlib import Path
from queue import Empty
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from social_media.src.config import Config, build_config
from social_media.src.dependencies import Dependencies
from social_media.src.pipeline.runner import run_pipeline
from social_media.src.ui.progress import (
    PHASE_ERROR,
    PHASE_EXPORT_COMPLETED,
    PHASE_EXTRACTION_COMPLETED,
    PHASE_EXTRACTION_STARTED,
    PHASE_FINISHED,
    PHASE_PIPELINE_STEP,
    ProgressEvent,
)
from social_media.src.ui.runner import execute_run, start_run_in_thread

_RUNNER_MODULE = "social_media.src.ui.runner"


def _make_config(tmp_path: Path) -> Config:
    return build_config(
        apify_token="test-token",
        output_dir=tmp_path / "output",
        data_dir=tmp_path / "data",
    )


def _make_raw_json(config: Config, run_id: str, items: list[dict[str, Any]]) -> Path:
    config.data_dir.mkdir(parents=True, exist_ok=True)
    raw_path = config.data_dir / f"raw_{run_id}.json"
    raw_path.write_text(json.dumps(items), encoding="utf-8")
    return raw_path


def _fake_run_pipeline(
    steps: list[Any],
    dfs: dict[str, pd.DataFrame],
    config: Config,
    deps: Dependencies,
    *,
    progress_callback: Any = None,
) -> dict[str, pd.DataFrame]:
    if progress_callback is not None:
        progress_callback("parse_step")
        progress_callback("timing_step")
    return {"posts": pd.DataFrame({"id": [1]})}


def _patch_orchestrator(
    raw_path: Path | None = None,
    extract_error: Exception | None = None,
):
    """Aplica os mocks das funções pesadas usadas por execute_run."""
    if extract_error is not None:
        extract_mock = AsyncMock(side_effect=extract_error)
    else:
        extract_mock = AsyncMock(return_value=raw_path)

    return (
        patch(f"{_RUNNER_MODULE}.extract", extract_mock),
        patch(f"{_RUNNER_MODULE}.run_pipeline", side_effect=_fake_run_pipeline),
        patch(f"{_RUNNER_MODULE}.export_xlsx"),
        patch(f"{_RUNNER_MODULE}.export_charts"),
        patch(f"{_RUNNER_MODULE}.configure_logging"),
        patch(f"{_RUNNER_MODULE}.set_run_id"),
    )


def test_execute_run_emits_progress_events(tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    run_id = "run-test-1"
    raw_path = _make_raw_json(config, run_id, [{"id": 1}, {"id": 2}, {"id": 3}])
    events: list[ProgressEvent] = []

    patches = _patch_orchestrator(raw_path=raw_path)
    with patches[0], patches[1], patches[2] as xlsx_mock, patches[3] as png_mock, patches[4], patches[5]:
        output_dir = asyncio.run(
            execute_run(["https://www.instagram.com/p/A/"], run_id, config, events.append)
        )

    assert output_dir == config.output_dir / run_id

    phases = [event.phase for event in events]
    assert phases == [
        PHASE_EXTRACTION_STARTED,
        PHASE_EXTRACTION_COMPLETED,
        PHASE_PIPELINE_STEP,
        PHASE_PIPELINE_STEP,
        PHASE_EXPORT_COMPLETED,
        PHASE_FINISHED,
    ]

    extraction_event = events[1]
    assert extraction_event.detail["items_count"] == 3
    assert "3" in extraction_event.message

    step_events = [e for e in events if e.phase == PHASE_PIPELINE_STEP]
    assert [e.detail["step"] for e in step_events] == ["parse_step", "timing_step"]

    expected_output = config.output_dir / run_id
    xlsx_mock.assert_called_once()
    assert xlsx_mock.call_args.args[1] == expected_output
    png_mock.assert_called_once()
    assert png_mock.call_args.args[1] == expected_output / "charts"


def test_execute_run_propagates_extract_error(tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    events: list[ProgressEvent] = []

    patches = _patch_orchestrator(extract_error=RuntimeError("falha no Apify"))
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        with pytest.raises(RuntimeError, match="falha no Apify"):
            asyncio.run(
                execute_run(
                    ["https://www.instagram.com/p/A/"], "run-x", config, events.append
                )
            )

    assert [event.phase for event in events] == [PHASE_EXTRACTION_STARTED]


def test_start_run_in_thread_success(tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    run_id = "run-thread-ok"
    raw_path = _make_raw_json(config, run_id, [{"id": 1}])

    patches = _patch_orchestrator(raw_path=raw_path)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        thread, events_queue, result = start_run_in_thread(
            ["https://www.instagram.com/p/A/"], run_id, config
        )
        thread.join(timeout=30)

    assert not thread.is_alive()
    assert result["status"] == "success"
    assert result["output_dir"] == str(config.output_dir / run_id)

    drained: list[ProgressEvent] = []
    while True:
        try:
            drained.append(events_queue.get_nowait())
        except Empty:
            break
    assert drained[-1].phase == PHASE_FINISHED


def test_start_run_in_thread_error(tmp_path: Path) -> None:
    config = _make_config(tmp_path)

    patches = _patch_orchestrator(extract_error=RuntimeError("falha no Apify"))
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        thread, events_queue, result = start_run_in_thread(
            ["https://www.instagram.com/p/A/"], "run-thread-err", config
        )
        thread.join(timeout=30)

    assert not thread.is_alive()
    assert result["status"] == "error"
    assert "falha no Apify" in result["error"]
    assert result["traceback"]

    drained: list[ProgressEvent] = []
    while True:
        try:
            drained.append(events_queue.get_nowait())
        except Empty:
            break
    assert drained[-1].phase == PHASE_ERROR
    assert "falha no Apify" in drained[-1].message


def test_run_pipeline_calls_progress_callback(tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    deps = Dependencies()
    step_names: list[str] = []

    def step_a(dfs: dict[str, pd.DataFrame], config: Config, deps: Dependencies) -> dict[str, pd.DataFrame]:
        return dfs

    def step_b(dfs: dict[str, pd.DataFrame], config: Config, deps: Dependencies) -> dict[str, pd.DataFrame]:
        return dfs

    result = run_pipeline(
        [step_a, step_b], {}, config, deps, progress_callback=step_names.append
    )

    assert result == {}
    assert step_names == ["step_a", "step_b"]


def test_run_pipeline_without_progress_callback_still_works(tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    deps = Dependencies()

    def step_a(dfs: dict[str, pd.DataFrame], config: Config, deps: Dependencies) -> dict[str, pd.DataFrame]:
        return {**dfs, "done": pd.DataFrame({"x": [1]})}

    result = run_pipeline([step_a], {}, config, deps)

    assert list(result) == ["done"]

"""Orquestração de execuções do pipeline para a interface web.

Reutiliza as mesmas funções de `social_media.src.main` (extração, pipeline e
exportadores), adicionando um callback de progresso e execução em thread de
fundo para não bloquear a UI do Streamlit.
"""

import asyncio
import json
import logging
import threading
import traceback
from pathlib import Path
from queue import Queue
from typing import Any

from social_media.src.config import Config
from social_media.src.dependencies import build_dependencies
from social_media.src.exporters.png import export_charts
from social_media.src.exporters.xlsx import export_xlsx
from social_media.src.extract.apify import extract
from social_media.src.log import configure_logging, set_run_id
from social_media.src.main import STEPS
from social_media.src.pipeline.runner import run_pipeline
from social_media.src.ui.progress import (
    PHASE_ERROR,
    PHASE_EXPORT_COMPLETED,
    PHASE_EXTRACTION_COMPLETED,
    PHASE_EXTRACTION_STARTED,
    PHASE_FINISHED,
    PHASE_PIPELINE_STEP,
    ProgressCallback,
    ProgressEvent,
)

logger = logging.getLogger(__name__)


def _count_extracted_items(raw_json_path: Path) -> int:
    """Conta os itens do JSON bruto salvo pela extração (0 em caso de falha)."""
    try:
        data = json.loads(raw_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning(
            "Não foi possível contar os itens extraídos.",
            extra={"raw_json_path": str(raw_json_path)},
        )
        return 0
    return len(data) if isinstance(data, list) else 0


async def execute_run(
    links: list[str],
    run_id: str,
    config: Config,
    on_progress: ProgressCallback,
) -> Path:
    """Executa o fluxo completo (extração → pipeline → exportação).

    Usa as mesmas funções de `social_media.src.main`, emitindo eventos de
    progresso através de `on_progress`.

    Args:
        links: URLs de posts do Instagram a processar.
        run_id: Identificador da execução.
        config: Configuração da aplicação.
        on_progress: Callback chamado a cada evento de progresso.

    Returns:
        Diretório de saída da execução (`output/{run_id}`).
    """
    set_run_id(run_id)
    configure_logging(config.log_level, config.log_format)

    logger.info(
        "Iniciando execução via interface web.",
        extra={"run_id": run_id, "links_count": len(links)},
    )

    deps = build_dependencies(config)

    on_progress(
        ProgressEvent(
            phase=PHASE_EXTRACTION_STARTED,
            message=f"Extração iniciada — chamando o ator {config.apify_actor}...",
            detail={"links_count": len(links)},
        )
    )
    raw_json_path = await extract(links, config, run_id)

    items_count = _count_extracted_items(raw_json_path)
    on_progress(
        ProgressEvent(
            phase=PHASE_EXTRACTION_COMPLETED,
            message=f"Extração concluída — {items_count} itens baixados.",
            detail={"items_count": items_count},
        )
    )

    def on_step(step_name: str) -> None:
        on_progress(
            ProgressEvent(
                phase=PHASE_PIPELINE_STEP,
                message=f"Pipeline em execução — etapa: {step_name}",
                detail={"step": step_name},
            )
        )

    initial_dfs: dict[str, Any] = {"raw_json_path": raw_json_path}
    dfs = run_pipeline(STEPS, initial_dfs, config, deps, progress_callback=on_step)

    output_root = config.output_dir / run_id
    export_xlsx(dfs, output_root, config)
    export_charts(dfs, output_root / "charts", config)

    on_progress(
        ProgressEvent(
            phase=PHASE_EXPORT_COMPLETED,
            message="Exportação concluída — XLSX e gráficos gerados.",
            detail={"output_dir": str(output_root)},
        )
    )
    on_progress(
        ProgressEvent(
            phase=PHASE_FINISHED,
            message="Execução finalizada com sucesso.",
            detail={"run_id": run_id, "output_dir": str(output_root)},
        )
    )

    logger.info(
        "Execução finalizada.",
        extra={"run_id": run_id, "output_root": str(output_root)},
    )
    return output_root


def start_run_in_thread(
    links: list[str],
    run_id: str,
    config: Config,
) -> tuple[threading.Thread, "Queue[ProgressEvent]", dict[str, Any]]:
    """Inicia `execute_run` em uma thread de fundo.

    A UI consome os eventos de progresso através da fila retornada, sem
    bloquear a thread principal do Streamlit.

    Returns:
        Tupla (thread, fila de eventos, caixa de resultado). A caixa de
        resultado é um dict preenchido ao final com as chaves "status"
        ("success" | "error"), "output_dir", "error" e "traceback".
    """
    events: Queue[ProgressEvent] = Queue()
    result: dict[str, Any] = {"status": "running", "output_dir": None, "error": None}

    def worker() -> None:
        try:
            output_dir = asyncio.run(execute_run(links, run_id, config, events.put))
        except Exception as exc:
            logger.exception(
                "Falha na execução.",
                extra={"run_id": run_id, "error": str(exc)},
            )
            result["status"] = "error"
            result["error"] = str(exc)
            result["traceback"] = traceback.format_exc()
            events.put(
                ProgressEvent(
                    phase=PHASE_ERROR,
                    message=f"Falha na execução: {exc}",
                    detail={"error": str(exc)},
                )
            )
        else:
            result["status"] = "success"
            result["output_dir"] = str(output_dir)

    thread = threading.Thread(
        target=worker,
        name=f"pipeline-run-{run_id[:8]}",
        daemon=True,
    )
    thread.start()
    return thread, events, result

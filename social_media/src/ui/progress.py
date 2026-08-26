"""Eventos de progresso emitidos pelo orquestrador de execução para a UI."""

from dataclasses import dataclass, field
from typing import Any, Callable

PHASE_EXTRACTION_STARTED = "extraction_started"
PHASE_EXTRACTION_COMPLETED = "extraction_completed"
PHASE_PIPELINE_STEP = "pipeline_step"
PHASE_EXPORT_COMPLETED = "export_completed"
PHASE_FINISHED = "finished"
PHASE_ERROR = "error"


@dataclass(frozen=True)
class ProgressEvent:
    """Evento de progresso de uma execução do pipeline.

    Attributes:
        phase: Fase da execução (uma das constantes PHASE_*).
        message: Mensagem amigável para exibição na UI.
        detail: Dados extras do evento (ex.: nome do step, quantidade de itens).
    """

    phase: str
    message: str
    detail: dict[str, Any] = field(default_factory=dict)


ProgressCallback = Callable[[ProgressEvent], None]

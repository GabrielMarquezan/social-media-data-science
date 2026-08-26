import logging
import json
import os
import sys

_run_id = None


class _TransformersAliasWarningFilter(logging.Filter):
    """Descarta avisos de módulos-alias deprecados do transformers.

    O transformers 5.x registra módulos de compatibilidade em `sys.modules`
    (ex.: `transformers.models.*.image_processing_*_fast`) que emitem um
    WARNING a qualquer acesso de atributo — incluindo `__path__`, acessado
    por ferramentas como o file watcher do Streamlit. Esses avisos são ruído
    e não indicam problema na aplicação.
    """

    _MESSAGE_NEEDLE = "this alias will be removed in future versions"

    def filter(self, record: logging.LogRecord) -> bool:
        return self._MESSAGE_NEEDLE not in record.getMessage()


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "run_id": _run_id or "none",
        }
        reserved = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "asctime",
        }
        for key, value in record.__dict__.items():
            if key not in reserved and not key.startswith("_"):
                data[key] = value
        return json.dumps(data, default=str)


def configure_logging(
    log_level: str | None = None,
    log_format: str | None = None,
) -> None:
    level = (log_level or os.getenv("LOG_LEVEL", "DEBUG")).upper()
    fmt = (log_format or os.getenv("LOG_FORMAT", "json")).lower()

    handler = logging.StreamHandler(sys.stderr)

    if fmt == "json":
        handler.setFormatter(_JSONFormatter())
    else:
        # Use standard Formatter directly, inject run_id via a simple lambda
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | run=%(run_id)s | %(message)s"
        )
        # Monkey-patch the format method to inject run_id
        original_format = formatter.format

        def format_with_run_id(record):
            record.run_id = _run_id or "none"
            return original_format(record)

        formatter.format = format_with_run_id
        handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Reduz ruído de bibliotecas externas nos logs estruturados
    for noisy_logger in (
        "apify_client",
        "matplotlib",
        "openpyxl",
        "PIL",
        "urllib3",
        "transformers",
        "torch",
    ):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    # O logger do transformers usa handler próprio com propagate=False, então
    # o filtro precisa ser aplicado diretamente nele (e não no root logger).
    transformers_logger = logging.getLogger("transformers")
    if not any(
        isinstance(f, _TransformersAliasWarningFilter) for f in transformers_logger.filters
    ):
        transformers_logger.addFilter(_TransformersAliasWarningFilter())

    logging.getLogger(__name__).debug(
        "Logging configured with level=%s and format=%s.",
        level,
        fmt,
        extra={"step": "configure_logging", "level": level, "format": fmt},
    )


def set_run_id(run_id: str | None) -> None:
    global _run_id
    _run_id = run_id
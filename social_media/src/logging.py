import logging
import json
import os
import sys

_run_id = None

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


def configure_logging() -> None:
    level = os.getenv("LOG_LEVEL", "DEBUG").upper()
    fmt = os.getenv("LOG_FORMAT", "json").lower()

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

    logging.getLogger(__name__).debug(
        "Logging configured with level=%s and format=%s.",
        level,
        fmt,
        extra={"step": "configure_logging", "level": level, "format": fmt},
    )


def set_run_id(run_id: str | None) -> None:
    global _run_id
    _run_id = run_id
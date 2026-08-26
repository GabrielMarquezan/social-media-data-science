import logging

from social_media.src.log import _TransformersAliasWarningFilter, configure_logging


def _make_record(message: str) -> logging.LogRecord:
    return logging.LogRecord(
        name="transformers",
        level=logging.WARNING,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )


def test_filter_drops_transformers_alias_warnings() -> None:
    record = _make_record(
        "Accessing `__path__` from `.models.vit.image_processing_vit`. "
        "Returning `__path__` instead. Behavior may be different and this "
        "alias will be removed in future versions."
    )
    assert _TransformersAliasWarningFilter().filter(record) is False


def test_filter_keeps_genuine_warnings() -> None:
    record = _make_record("PyTorch was not found. Models won't be available.")
    assert _TransformersAliasWarningFilter().filter(record) is True


def test_configure_logging_installs_filter_idempotently() -> None:
    configure_logging("WARNING", "text")
    configure_logging("WARNING", "text")

    transformers_logger = logging.getLogger("transformers")
    alias_filters = [
        f for f in transformers_logger.filters
        if isinstance(f, _TransformersAliasWarningFilter)
    ]
    assert len(alias_filters) == 1

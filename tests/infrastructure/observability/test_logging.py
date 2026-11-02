import logging

from app.infrastructure.observability.redaction import silence_url_loggers


def test_silence_url_loggers_hides_info_logs_that_print_request_urls():
    try:
        silence_url_loggers()

        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("httpcore").level == logging.WARNING
        assert not logging.getLogger("httpx").isEnabledFor(logging.INFO)
    finally:
        logging.getLogger("httpx").setLevel(logging.NOTSET)
        logging.getLogger("httpcore").setLevel(logging.NOTSET)

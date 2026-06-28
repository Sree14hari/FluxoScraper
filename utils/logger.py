from __future__ import annotations

import logging

from rich.logging import RichHandler


def setup_logger() -> logging.Logger:
    """Configure and return the application logger with rich formatting."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)],
    )
    return logging.getLogger("fluxo")

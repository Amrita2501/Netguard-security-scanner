"""
Centralized logging setup.

Call `configure_logging()` once, as early as possible (before other app
modules that create loggers are imported/run their module-level code),
so every `logging.getLogger("netguard.<module>")` call across the app
shares one consistent format and level.
"""
import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger("netguard")
    if root.handlers:
        return  # already configured (e.g. re-imported under a test runner)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(getattr(logging, level, logging.INFO))
    root.propagate = False

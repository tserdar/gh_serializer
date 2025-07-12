"""Utility to save structured data to a JSON file."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def save_to_json(data: list[dict[str, Any]], output_path: str) -> None:
    """Save structured data to a JSON file.

    Args:
        data: A list of dictionaries to serialize as JSON.
        output_path: Path where the JSON file will be saved.

    Logs:
        Logs errors if writing or serialization fails.

    """
    try:
        with Path(output_path).open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("Saved data to JSON: %s", output_path)
    except (OSError, TypeError):
        logger.exception("Failed to write JSON to %s", output_path)

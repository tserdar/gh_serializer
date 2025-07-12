"""Script that contains fetch functionality for gh_serializer."""

from __future__ import annotations

import logging
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from requests.exceptions import RequestException

from gh_serializer.static.file_types import SUPPORTED_EXTENSIONS, SUPPORTED_STEMS

logger = logging.getLogger(__name__)


def parse_gh_repo_url(repo_url: str) -> tuple[str, str]:
    """Parse GitHub repository URL into owner and repository name."""
    parts = urlparse(repo_url)
    if "github.com" not in parts.netloc:
        logger.error("URL must be from github.com: %s", repo_url)
        return "", ""

    path_parts = parts.path.strip("/").split("/")
    if len(path_parts) < 2:  # noqa: PLR2004
        logger.error("GitHub URL is missing owner or repo name: %s", repo_url)
        return "", ""

    owner, repo = path_parts[0], path_parts[1]
    logger.debug("Parsed GitHub URL: owner=%s, repo=%s", owner, repo)
    return owner, repo


def is_supported_file(file_path: str) -> bool:
    """Check whether the file is supported based on its extension or stem."""
    path = Path(file_path)
    return path.suffix.lower() in SUPPORTED_EXTENSIONS or path.stem in SUPPORTED_STEMS


def download_and_extract_repo_zip(owner: str, repo: str, branch: str = "main") -> Path | None:
    """Download a GitHub repository as a ZIP and extract it."""
    zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
    logger.info("Downloading ZIP from: %s", zip_url)

    try:
        response = requests.get(zip_url, timeout=15)
        response.raise_for_status()
    except RequestException:
        logger.exception("Failed to download ZIP: %s", zip_url)
        return None

    temp_dir = Path(tempfile.mkdtemp())
    zip_path = temp_dir / f"{repo}.zip"

    try:
        zip_path.write_bytes(response.content)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)
    except Exception:
        logger.exception("Failed to extract ZIP file: %s", zip_path)
        return None

    extracted_path = temp_dir / f"{repo}-{branch}"
    logger.debug("Repository extracted to: %s", extracted_path)
    return extracted_path


def fetch_repo_via_zip(repo_url: str, branch: str = "main") -> list[dict[str, Any]]:
    """Fetch supported files from a GitHub repository ZIP."""
    owner, repo = parse_gh_repo_url(repo_url)
    if not owner or not repo:
        logger.warning("Invalid GitHub URL: %s", repo_url)
        return []

    repo_path = download_and_extract_repo_zip(owner, repo, branch)
    if not repo_path or not repo_path.exists():
        logger.warning("Could not download or extract repo: %s", repo_url)
        return []

    files: list[dict[str, Any]] = []

    for root, _, filenames in os.walk(repo_path):
        for filename in filenames:
            full_path = Path(root) / filename
            rel_path = full_path.relative_to(repo_path)

            if not is_supported_file(str(full_path)):
                logger.debug("Skipping unsupported file: %s", rel_path)
                continue

            try:
                content = full_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError) as exc:
                logger.warning("Skipping %s due to read error: %s", rel_path, exc)
                continue

            files.append(
                {
                    "path": rel_path.as_posix(),
                    "language": full_path.suffix.lstrip("."),
                    "type": "code",
                    "content": content,
                },
            )

    logger.info("Fetched %d supported files from %s", len(files), repo_url)
    return files

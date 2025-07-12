"""Demo to test the serializer."""

from gh_serializer.fetch import fetch_repo_via_zip
from gh_serializer.serialize import save_to_json

files = fetch_repo_via_zip("https://github.com/tserdar/gh_serializer", "main")
save_to_json(files, "gh_serializer.json")

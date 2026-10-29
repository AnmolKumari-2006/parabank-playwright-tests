"""Reads JSON files from the test_data folder."""
import json
from pathlib import Path

TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "test_data"


def load_json(file_name: str):
    with open(TEST_DATA_DIR / file_name, encoding="utf-8") as f:
        return json.load(f)

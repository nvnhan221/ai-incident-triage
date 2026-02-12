#!/usr/bin/env python3
"""Ingest file sample_logs_y20ki9r6.json vào Log Consumer (POST /ingest/batch)."""
import json
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Cần cài: pip install httpx")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
SAMPLE = SCRIPT_DIR / "sample_logs_y20ki9r6.json"
URL = "http://localhost:8001/ingest/batch"

def main():
    if not SAMPLE.exists():
        print(f"Không tìm thấy {SAMPLE}")
        sys.exit(1)
    with open(SAMPLE, encoding="utf-8") as f:
        logs = json.load(f)
    print(f"Đang gửi {len(logs)} log đến {URL} ...")
    r = httpx.post(URL, json=logs, timeout=30.0)
    r.raise_for_status()
    data = r.json()
    print("OK:", data)

if __name__ == "__main__":
    main()

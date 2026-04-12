#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import polib


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def apply_entry(repo_root: Path, po_rel: str, entry_payload: dict[str, Any]) -> bool:
    translated = (entry_payload.get("t") or "").strip()
    if not translated:
        return False

    po_path = (repo_root / po_rel).resolve()
    entry_index = int(entry_payload["i"])
    expected_msgid = entry_payload["id"]

    po = polib.pofile(str(po_path))
    if entry_index < 0 or entry_index >= len(po):
        raise IndexError(f"entry_index out of range: {po_rel}#{entry_index}")

    entry = po[entry_index]
    if entry.msgid != expected_msgid:
        raise ValueError(
            "Entry mismatch while applying translation: "
            f"{po_rel}#{entry_index} expected msgid {expected_msgid!r}, got {entry.msgid!r}"
        )

    entry.msgstr = translated
    po.save(str(po_path))
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply compact translation payload back into .po files.")
    parser.add_argument("--input", required=True, help="Input JSON payload path.")
    parser.add_argument("--root", default=".", help="Repository root for resolving po_path.")
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    input_path = Path(args.input).resolve()
    payload = load_payload(input_path)
    if payload.get("version") != 2:
        raise ValueError("Unsupported payload version. Expected version 2.")
    files = payload.get("files", [])

    updated = 0
    touched_files: set[Path] = set()
    for file_payload in files:
        po_rel = file_payload["path"]
        file_updated = False
        for entry_payload in file_payload.get("entries", []):
            if apply_entry(repo_root, po_rel, entry_payload):
                updated += 1
                file_updated = True
        if file_updated:
            touched_files.add((repo_root / po_rel).resolve())

    print(f"Applied {updated} translations across {len(touched_files)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
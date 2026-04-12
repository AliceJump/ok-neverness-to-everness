#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any

import polib


SUPPORTED_LOCALES = {"en_US", "es_ES", "ja_JP", "ko_KR", "zh_CN", "zh_TW"}


def infer_locale_from_path(po_path: Path) -> str:
    parts = po_path.as_posix().split("/")
    for i, part in enumerate(parts):
        if part == "i18n" and i + 1 < len(parts):
            return parts[i + 1]
    return "unknown"


def display_width(text: str) -> int:
    width = 0
    for ch in text:
        if unicodedata.combining(ch):
            continue
        width += 2 if unicodedata.east_asian_width(ch) in {"W", "F"} else 1
    return width


def _char_ratio(text: str, predicate) -> float:
    chars = [ch for ch in text if not ch.isspace()]
    if not chars:
        return 0.0
    return sum(1 for ch in chars if predicate(ch)) / len(chars)


def looks_like_locale_text(text: str, locale: str) -> bool:
    locale = locale.lower()
    if not text.strip():
        return False

    if locale.startswith("en"):
        return _char_ratio(text, lambda c: c.isascii() and (c.isalpha() or c.isdigit() or c in "_.,!?;:'\"-()[]{}<>/@%+*=#&")) >= 0.85
    if locale.startswith("es"):
        return _char_ratio(text, lambda c: c.isascii() or c in "áéíóúüñÁÉÍÓÚÜÑ¡¿") >= 0.85
    if locale.startswith("zh"):
        return _char_ratio(text, lambda c: "\u4e00" <= c <= "\u9fff") >= 0.45
    if locale.startswith("ja"):
        return _char_ratio(text, lambda c: ("\u3040" <= c <= "\u309f") or ("\u30a0" <= c <= "\u30ff") or ("\u4e00" <= c <= "\u9fff")) >= 0.45
    if locale.startswith("ko"):
        return _char_ratio(text, lambda c: "\uac00" <= c <= "\ud7a3") >= 0.45
    return False


def iter_po_files(input_path: Path) -> list[Path]:
    if input_path.is_file() and input_path.suffix.lower() == ".po":
        return [input_path]
    return sorted(p for p in input_path.rglob("*.po") if p.is_file())


def build_entry(
    target_locale: str,
    entry_index: int,
    entry: polib.POEntry,
    include_translated: bool,
) -> dict[str, Any] | None:
    if target_locale not in SUPPORTED_LOCALES:
        return None
    if entry.obsolete:
        return None
    if not entry.msgid:
        return None
    if not include_translated and entry.msgstr.strip():
        return None

    msgid_already_target = looks_like_locale_text(entry.msgid, target_locale)
    if msgid_already_target:
        return None

    payload_entry = {
        "i": entry_index,
        "id": entry.msgid,
        "w": display_width(entry.msgid),
        "t": "",
    }
    if include_translated and entry.msgstr.strip():
        payload_entry["cur"] = entry.msgstr
    if entry.msgctxt:
        payload_entry["ctx"] = entry.msgctxt
    if entry.msgid_plural:
        payload_entry["idp"] = entry.msgid_plural
    return payload_entry


def write_output(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_json = json.dumps(payload, ensure_ascii=False, indent=2)
    output_path.write_text(f"{output_json}\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract translation tasks from .po files.")
    parser.add_argument("--input", required=True, help="Input .po file or folder path.")
    parser.add_argument("--output", required=True, help="Output JSON file path.")
    parser.add_argument(
        "--locales",
        nargs="+",
        help="Filter by specific locales (e.g., --locales zh_CN en_US). If not specified, process all locales.",
    )
    parser.add_argument(
        "--include-translated",
        action="store_true",
        help="Include entries that already have msgstr. Useful for review/rewriting existing translations.",
    )
    parser.add_argument("--root", default=".", help="Repository root for relative paths.")
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    po_files = iter_po_files(input_path)
    files_payload: list[dict[str, Any]] = []
    locale_filter = set(args.locales) if args.locales else None

    for po_file in po_files:
        target_locale = infer_locale_from_path(po_file)
        if target_locale not in SUPPORTED_LOCALES:
            continue
        if locale_filter and target_locale not in locale_filter:
            continue
        po = polib.pofile(str(po_file))
        entries_payload: list[dict[str, Any]] = []
        for idx, entry in enumerate(po):
            item = build_entry(target_locale, idx, entry, args.include_translated)
            if item:
                entries_payload.append(item)
        if entries_payload:
            files_payload.append(
                {
                    "path": po_file.relative_to(repo_root).as_posix(),
                    "locale": target_locale,
                    "entries": entries_payload,
                }
            )

    total_entries = sum(len(file_payload["entries"]) for file_payload in files_payload)

    payload = {
        "version": 2,
        "note": "Fill entry.t only; keep empty if no change. entry.cur is read-only context.",
        "files": files_payload,
    }

    write_output(output_path, payload)
    print(f"Extracted {total_entries} items across {len(files_payload)} files -> {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
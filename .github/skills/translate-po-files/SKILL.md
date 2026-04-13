---
name: translate-po-files
description: 'Translate gettext .po files under i18n with folder-locale targeting, UI-width-aware phrasing, terminology consistency, and same-language blank rules. Use when localizing game/UI strings, updating msgstr values, or reviewing translation quality.'
argument-hint: 'Provide one or more .po paths or folders under i18n (for example: i18n/zh_CN/LC_MESSAGES/ok.po or i18n/).'
user-invocable: true
---

# Translate PO Files

## Purpose
- Translate gettext `.po` entries under `i18n/*/LC_MESSAGES/*.po`.
- Infer target language from locale folder.
- Keep translation focused and deterministic via extract-to-file -> translate -> apply-from-file.

## Supported Locales
The project contains exactly these locales under `i18n/`:
- `en_US` — English (United States)
- `es_ES` — Spanish (Spain)
- `ja_JP` — Japanese
- `ko_KR` — Korean
- `zh_CN` — Simplified Chinese
- `zh_TW` — Traditional Chinese

## Quick Workflow
1. Run extraction script to write UTF-8 JSON tasks to a file.
2. Agent fills only `entry.t` in that JSON file.
3. Run apply script with that JSON file to write back non-empty `entry.t`.

## Script Parameters
### extract_po_for_translation.py
- `--input` (required): one `.po` file or a folder like `i18n/`
- `--output` (required): output JSON file path for the translation task payload
- `--locales` (optional): only process specific locales, e.g. `--locales zh_CN zh_TW`
- `--include-translated` (optional): also output entries that already have `msgstr` for review/rewriting
- `--root` (optional): repository root, default `.`

Default behavior: already translated entries are skipped.

### apply_po_translations.py
- `--input` (required): input JSON file path containing translated entries
- `--root` (optional): repository root, default `.`

This skill uses a file-based workflow only. Do not pipe JSON through stdin.

## Minimal Examples
```bash
# Extract untranslated entries from all locales into a UTF-8 JSON file
./.venv/Scripts/python.exe .github/skills/translate-po-files/scripts/extract_po_for_translation.py --input i18n --output translation-todo.json

# Extract untranslated entries from selected locales
./.venv/Scripts/python.exe .github/skills/translate-po-files/scripts/extract_po_for_translation.py --input i18n --output translation-todo.json --locales zh_CN zh_TW

# Extract including existing translations (review mode)
./.venv/Scripts/python.exe .github/skills/translate-po-files/scripts/extract_po_for_translation.py --input i18n --output translation-review.json --include-translated
```

```bash
# Apply translated JSON from a file
./.venv/Scripts/python.exe .github/skills/translate-po-files/scripts/apply_po_translations.py --input translation-done.json
```

## Payload Contract
- Agent can edit only `files[*].entries[*].t`.
- `entry.t == ""` means no write-back.
- `entry.cur` may appear in review mode (`--include-translated`) and is read-only context.

Extractor/apply behavior is handled by Python scripts:
- Extractor decides which PO entries are emitted into the JSON file.
- Apply reads the translated JSON file and writes non-empty `entry.t` back to PO entries.

## Rules
- Keep placeholders unchanged: `%s`, `%d`, `{name}`, `\\n`.
- Focus on JSON editing: provide translation only in `entry.t` when needed.
- Reuse consistent terminology in the same file first, then project-wide.
- In validation or review-mode workflows, if the user intentionally clears an existing `msgstr` to have it regenerated, treat that as intentional test setup and do not auto-revert the regenerated translation unless the user asks.
- Do not edit payload structure fields other than `entry.t`.

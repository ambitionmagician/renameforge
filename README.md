# RenameForge

by Dr. Brent Allen Jensen

Safe batch file renaming: preview everything first (dry-run is the
default), rename only when you say `--apply`, never overwrite an
existing file, and undo a whole batch from its log.

## Quickstart

```bash
python3 renameforge.py ./photos --spaces-to-dash          # preview
python3 renameforge.py ./photos --spaces-to-dash --apply  # do it
python3 renameforge.py ./docs --prefix "2026-" --ext ".txt,.md" --apply
python3 renameforge.py ./data --pattern "(\d+)" --replace "file_\1" --apply
python3 renameforge.py ./photos --undo renameforge-log.json
```

## Transformations (pick one)

| Option | What it does |
|---|---|
| `--pattern REGEX --replace TEMPLATE` | Regex substitution on the filename; TEMPLATE may use `\1` groups |
| `--prefix TEXT` | Add a prefix to every filename |
| `--suffix TEXT` | Append text to every filename (after the extension) |
| `--lower` | Lowercase every filename |
| `--spaces-to-dash` | Replace spaces with dashes |

`--ext ".txt,.md"` limits which files are considered. Files are
processed in sorted order, in one directory (not recursive).

## Safety rails

- **Dry-run by default** — nothing changes until `--apply`.
- **Never overwrites** — a rename whose target already exists is
  skipped with a warning.
- **Undo log** — `--apply` writes `renameforge-log.json` into the
  directory; `--undo <log>` reverses the batch in reverse order.

## Requirements

- Python 3.10+, standard library only

## Support this work

If this tool saved you time or taught you something, donations keep the work going:

- BTC: 15McijPo79Zx58NGyEf2PvaPtGqGmpztWn
- ETH: 0x8C25164E9234E6A30b8E44485B79c5cE8419cF2B

## License

MIT — see [LICENSE](LICENSE).

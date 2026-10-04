# continuity-check

A small checker for a continuity folder. Point it at a directory. It looks for a fixed list of markdown files, says which ones are missing, and prints a short wake-up card for each file that is there: the filename and the first 12 non-empty lines (stripped, long lines cut).

It checks presence and the opening lines. It does not judge whether the notes are any good.

## Run

```bash
python3 check.py examples/sample-shelf --config examples/config.json
python3 check.py examples/sample-shelf-full --config examples/config.json
```

The first command is the incomplete fixture (`HANDOFF.md` is left out) and exits 1. The second has every file and exits 0.

Without `--config`, the expected names are `IDENTITY.md`, `RAILS.md`, `BOUNDARIES.md`, `CURRENT.md`, and `HANDOFF.md`.

```bash
python3 check.py path/to/folder
```

Exit codes: `0` if every expected file is present, `1` if any are missing, `2` if the folder or config cannot be used.

## What changed

After a first look, `changed.py` remembers presence and wake-up lines in a small state file next to the script on this computer. Later runs print only what changed (newly present, newly missing, or different wake-up lines). The state file is gitignored and is never stored inside the shelf you point at.

```bash
python3 changed.py path/to/folder
```

Same `--config` flag as `check.py`. Exit `0` on the first look or when nothing changed, `1` when something changed, `2` if the folder or config cannot be used.

## Change the filename list

Edit `examples/config.json`, or pass another file with `--config`. The file is JSON (also valid as a tiny YAML document) shaped like this:

```json
{
  "files": [
    "IDENTITY.md",
    "RAILS.md",
    "BOUNDARIES.md",
    "CURRENT.md",
    "HANDOFF.md"
  ]
}
```

Names are bare filenames, not paths. Python 3 and the standard library only. No install step.

## Local page

From the repo directory, on the computer that has the folder:

```bash
python3 serve.py
```

Then open http://127.0.0.1:8765/ in a browser on that same computer. The server listens only on 127.0.0.1 and refuses to listen on 0.0.0.0, so another machine cannot open the page. It reads the folder path you type and, if you give one, the config file path. It does not upload those notes.

Paste the full path of the folder you cloned, then one of these paths under it. You do not need a private shelf:

- `examples/sample-shelf` is missing `HANDOFF.md` (the checker exits 1).
- `examples/sample-shelf-full` has every expected file (the checker exits 0).

Leave the config box empty, or paste the full path to `examples/config.json`. Ctrl-C stops the server.

# Manotron Documentation

Manotron scans a folder recursively, extracts invoice deduction rows with
OpenAI, stores them in SQLite, and exports them to Excel.

## Requirements

- Apple Silicon Mac
- An OpenAI API key
- Internet access during installation and extraction

The installed program is a standalone binary. Python, Git, and `uv` are not
required on the target Mac.

## Installation

Run:

```bash
curl -LsSf https://raw.githubusercontent.com/eljoserass/manotron/master/scripts/install.sh | bash
```

The installer:

1. Downloads the latest macOS ARM64 release.
2. Verifies its SHA-256 checksum.
3. Installs `manotron` in `~/.local/bin`.
4. Validates the supplied OpenAI API key.
5. Asks which folder should be scanned.
6. Optionally configures automatic scans.

If `manotron` is not found after installation, add this to your shell config:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Basic Use

Scan the configured folder:

```bash
manotron scan
```

Export all stored invoice lines:

```bash
manotron export
```

Export to a specific file:

```bash
manotron export --out ~/Desktop/salidas.xlsx
```

Filter by invoice date:

```bash
manotron export --from 2026-01-01 --to 2026-06-30
```

## How Scanning Works

- Every supported file inside the configured folder is found recursively.
- A SHA-256 hash identifies files already processed.
- New files are sent to the configured OpenAI model.
- Extracted invoices, product lines, and location deductions are stored in
  SQLite.
- Repeated invoice reference IDs are allowed. Only identical file hashes are
  skipped.
- Failed files remain recorded with their error and are not silently discarded.

Supported images:

```text
gif, jpeg, jpg, png, webp
```

Other accepted files:

```text
csv, doc, docx, html, json, md, odt, pdf, ppt, pptx,
rtf, tsv, txt, xls, xlsx, xml
```

PDFs and document files use OpenAI file input. Images use image input.

## Extracted Data

An invoice can contain several product lines. Each product line can deduct stock
from several locations.

Example:

```text
invoice_reference_id: INV-001
product_reference_id: PROD-42
quantity_deducted: 5
product_locations: A-01;B-07
locations_quantity: A-01::2;B-07::3
```

Manotron keeps both the flattened values used for Excel and normalized
`line_location_deductions` rows in SQLite.

Current extraction rules:

- Handwritten digits beside a location become that location's deduction.
- A checkmark with no digit assigns the full product quantity to that location.
- Likely rows are preferred over dropping uncertain data.
- The raw structured model response is stored with the invoice.

The prompt and invoice terminology are centralized in
`src/manotron/prompts.py`. Constants such as `LOCATION_KEYWORD` can be changed
when the real invoice vocabulary is known.

## Configuration

Show the active configuration:

```bash
manotron config show
```

Change the scanned folder:

```bash
manotron config set-folder /path/to/invoices
```

Change the extraction model:

```bash
manotron config set-model gpt-5-mini
```

Run onboarding again:

```bash
manotron init --folder /path/to/invoices --api-key "YOUR_KEY"
```

`OPENAI_API_KEY` overrides the key saved in the config for the current process:

```bash
OPENAI_API_KEY="YOUR_KEY" manotron scan
```

## Automatic Scans

Times use 24-hour `HH:MM` format.

Every day:

```bash
manotron schedule set --daily 21:30
```

Monday through Friday:

```bash
manotron schedule set --weekdays 08:00
```

Once a week:

```bash
manotron schedule set --weekly-day mon --weekly-time 07:30
```

Every six hours:

```bash
manotron schedule set --every-hours 6
```

Inspect or remove the schedule:

```bash
manotron schedule show
manotron schedule clear
```

Scheduling currently uses the user's crontab. Scan output is written to the
Manotron log directory.

## Local Files

On macOS, Manotron uses the standard user application directories:

```text
Configuration: ~/Library/Application Support/manotron/config.json
Database:      ~/Library/Application Support/manotron/manotron.sqlite3
Scan log:      ~/Library/Logs/manotron/scan.log
Binary:        ~/.local/bin/manotron
```

The config file is created with user-only permissions. The API key is stored
locally unless `OPENAI_API_KEY` is used instead.

## Development

Development dependencies are managed with `uv`:

```bash
uv sync
uv run pytest -q
uv run manotron --help
```

Build a standalone binary for the current operating system:

```bash
scripts/build_binary.sh
```

PyInstaller cannot cross-compile the macOS binary from Linux. Tagged releases
are built on an Apple Silicon GitHub Actions runner:

```bash
git tag -a v0.1.2 -m "manotron v0.1.2"
git push origin v0.1.2
```

The release workflow runs tests, builds and signs the binary, verifies the
installer, and publishes:

```text
manotron-macos-arm64
manotron-macos-arm64.sha256
```

## Useful Links

- Releases: https://github.com/eljoserass/manotron/releases
- Latest binary: https://github.com/eljoserass/manotron/releases/latest
- CLI help: `manotron --help`


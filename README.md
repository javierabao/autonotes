# AutoNotes

A Python application that uses OCR to extract text from images and formats it using LLM technology.

## Installation

1. Make sure you have Tesseract OCR installed on your system
2. Install the Python dependencies using Poetry:
```bash
poetry install
```

## Quickstart

1. Install system deps (Tesseract) if you plan to use OCR:

```bash
# macOS (Homebrew)
brew install tesseract
```

2. Install Python dependencies (Poetry recommended):

```bash
poetry install
```

3. Run the API server locally:

```bash
poetry run uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

Open http://127.0.0.1:8000/ in your browser for the demo UI.

## API (POST /process)

Endpoint: POST /process

Form fields:
- `file` (UploadFile) — required for image input; the filename is used for output naming
- `output_format` (str) — `docx` (default) or `md`/`markdown`
- `preview` (str) — set to `true` to return JSON with the formatted markdown instead of a file
- `markdown_content` (str) — optionally send pre-formatted markdown directly (skip OCR/LLM)

Example: send markdown and download a DOCX (curl):

```bash
curl -X POST 'http://127.0.0.1:8000/process' \
	-F 'file=@/dev/null;filename=test' \
	-F 'output_format=docx' \
	-F 'markdown_content=# Title\n\nSome **bold** text.' \
	--output test.docx
```

Example: request a JSON preview of the formatted markdown:

```bash
curl -X POST 'http://127.0.0.1:8000/process' \
	-F 'file=@/dev/null;filename=preview' \
	-F 'output_format=md' \
	-F 'preview=true' \
	-F 'markdown_content=# Draft\n\ntext' \
	| jq .
```

## Notes & Troubleshooting

- If you see a FileNotFoundError when downloading the generated file, it can be caused by the temporary output directory being removed before the server finishes streaming the file. The server now uses a BackgroundTask to remove the temporary directory only after the response is fully sent — restart the server after pulling the latest changes.
- When running with `--reload` (development mode), the auto-reloader can restart the process during active requests; this can also cause temporary files to become inaccessible. For reliable file delivery during tests, run without `--reload`.
- The LLM tokenizer/model may emit intermediate markers like `<think>` or `</think>`. The formatter strips lone tags and removes any `<think>...</think>` blocks — if you still see artifacts, please save the formatted markdown and paste an example into an issue.
- If you use Hugging Face models locally, you may see a `TOKENIZERS_PARALLELISM` warning. Set `TOKENIZERS_PARALLELISM=false` in your environment to silence it, or avoid creating tokenizers before forking workers.

## Development

- Tests: none included by default; add unit tests in `tests/` for `ocr_formatter.formatter` and `ocr_formatter.ocr` when you add functionality.
- Style: follow the project's existing code style.

## Requirements

- Python 3.12+
- Tesseract OCR
- If you use an LLM model that requires API keys or local model weights, follow that model's setup instructions.

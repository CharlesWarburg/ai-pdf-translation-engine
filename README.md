# AI PDF Translator

A production-style document translation service built with FastAPI and the OpenAI Agents SDK. Upload a PDF, choose a target language, and download a translated PDF.

## Features

- PDF upload and translation
- Multi-language support (English, French, Spanish, German)
- Chunked translation pipeline with parallel processing
- Unicode-safe PDF rendering (DejaVu Sans embedded, width-based wrapping)
- Structured JSON error contract
- Dockerised for consistent local execution

## Architecture

Upload → Extract → Chunk → Parallel translate → Reassemble → Render PDF

## Tech Stack

Python · FastAPI · OpenAI Agents SDK · ReportLab · Docker

## Run locally

```bash
cp .env.example .env
docker compose up --build
```

Open **http://localhost:8000**

## Error responses

All errors are JSON only:

```json
{"code": "<error_code>", "message": "<message>"}
```

| Status | Code | When |
|--------|------|------|
| 400 | `bad_request` | Unsupported language, oversized file, or no extractable text |
| 400 | `unsupported_file` | File is not PDF |
| 400 | `unsupported_media_type` | Wrong Content-Type |
| 502 | `upstream_error` | Transient upstream failure |
| 500 | `translation_failed` | Permanent upstream failure |
| 500 | `internal_error` | Unexpected error |

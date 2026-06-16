# Docker + OpenAI Setup Guide

This guide is for someone running the project locally with Docker and an OpenAI API key.

## What This Project Uses

- Docker to run the FastAPI app in a container
- `docker-compose.yml` to start the service
- `.env` for configuration
- OpenAI for the translation step
- FastAPI OpenAPI docs at `http://localhost:8000/docs`

## 1. Prerequisites

Install these first:

- Docker Desktop
- An OpenAI API key

Check Docker is available:

```bash
docker --version
docker compose version
```

## 2. Open the Project

In a terminal, move into the project folder:

```bash
cd /Users/charleswarburg/Desktop/Dev/ai-pdf-translation-engine
```

## 3. Create Your Environment File

Copy the example file:

```bash
cp .env.example .env
```

Open `.env` and set your API key:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

Optional settings:

```env
# Use the default OpenAI API endpoint unless you need a compatible provider
OPENAI_BASE_URL=https://api.openai.com/v1

# Default translation model used by the app
TRANSLATION_MODEL=gpt-4o-mini

# Max upload size in MB
MAX_UPLOAD_MB=20
```

## 4. Build and Start the App

Run:

```bash
docker compose up --build
```

What this does:

- Builds the image from the `Dockerfile`
- Installs Python dependencies
- Installs the DejaVu font used for Unicode PDF output
- Starts the FastAPI app on port `8000`

## 5. Open the App

Once the container is running, open:

- Web app: `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

If the app is running correctly, `/health` returns JSON similar to:

```json
{
  "status": "ok",
  "app": "AI PDF Translator",
  "environment": "local"
}
```

## 6. Test Translation in the Browser

1. Open `http://localhost:8000`
2. Upload a PDF
3. Choose a target language
4. Submit the form
5. Download the translated PDF

Supported target languages in the current app:

- English
- French
- Spanish
- German

## 7. Test the API from OpenAPI Docs

Open:

```text
http://localhost:8000/docs
```

Then:

1. Expand `POST /translate`
2. Click `Try it out`
3. Upload a `.pdf` file
4. Enter `French`, `Spanish`, `German`, or `English`
5. Click `Execute`

The endpoint returns a translated PDF file when successful.

## 8. Test the API with cURL

Example request:

```bash
curl -X POST "http://localhost:8000/translate" \
  -F "file=@test-pdfs/stress_mixed_styles_4p.pdf;type=application/pdf" \
  -F "target_language=French" \
  --output translated.pdf
```

If successful, the translated file will be saved as `translated.pdf`.

## 9. Stop the App

Press `Ctrl+C` in the terminal running Docker Compose.

If you want to stop and remove the container:

```bash
docker compose down
```

## 10. Common Issues

### Missing API key

If `OPENAI_API_KEY` is missing or invalid, translation requests will fail when the app tries to call OpenAI.

Fix:

- Check that `.env` exists
- Check that `OPENAI_API_KEY` is set correctly
- Restart the container after editing `.env`

## Unsupported file type

The `/translate` endpoint only accepts PDF files.

Fix:

- Upload a file ending in `.pdf`
- Make sure the upload content type is `application/pdf`

## Unsupported language

The app currently only supports:

- English
- French
- Spanish
- German

Use one of those exact values in the form or API request.

## Port 8000 already in use

If Docker cannot start because port `8000` is busy, stop the other process using that port or change the port mapping in `docker-compose.yml`.

## 11. Files Worth Knowing

- `docker-compose.yml`: starts the app container
- `Dockerfile`: defines the Python image and startup command
- `.env.example`: template for required environment variables
- `app/main.py`: FastAPI application entrypoint
- `app/routers/translate.py`: translation endpoint
- `app/config.py`: environment variable loading

## 12. Submission Summary

If you need a short explanation for a reviewer:

1. Add your OpenAI API key to `.env`
2. Run `docker compose up --build`
3. Open `http://localhost:8000`
4. Upload a PDF and choose a supported language
5. Use `http://localhost:8000/docs` to test the API directly through FastAPI's OpenAPI interface

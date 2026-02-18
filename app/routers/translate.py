import logging

from fastapi import APIRouter, File, Form, Request, UploadFile

from ..services import translation
from ..utils import errors


router = APIRouter(prefix="/translate", tags=["translate"])
logger = logging.getLogger(__name__)

ALLOWED_LANGUAGES = {"English", "French", "Spanish", "German"}


@router.post("")
async def translate_pdf(
    request: Request,
    file: UploadFile = File(...),
    target_language: str = Form(..., description="Target language for translation, e.g. 'French'"),
):
    """Translate an uploaded PDF into the target language."""

    request_id = getattr(request.state, "request_id", None)

    if target_language not in ALLOWED_LANGUAGES:
        return errors.error_response(400, "bad_request", "Unsupported target language.")

    if not file.filename.lower().endswith(".pdf"):
        return errors.error_response(400, "unsupported_file", "Only PDF uploads are supported at the moment.")

    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        return errors.error_response(
            400, "unsupported_media_type", f"Unexpected content-type: {file.content_type}"
        )

    try:
        result = await translation.translate_pdf_file(
            file=file,
            target_language=target_language,
            request_id=request_id,
        )
    except errors.UserInputError as exc:
        return errors.error_response(400, "bad_request", str(exc))
    except errors.TransientUpstreamError:
        return errors.error_response(
            502, "upstream_error", "Upstream translation service is temporarily unavailable."
        )
    except errors.PermanentUpstreamError:
        return errors.error_response(500, "translation_failed", "Translation failed.")
    except Exception:  # pragma: no cover - safety net
        logger.exception(
            "unexpected_error_during_translation request_id=%s filename=%s",
            request_id,
            file.filename,
        )
        return errors.error_response(500, "internal_error", "Unexpected error during translation.")

    logger.info(
        "translation_http_completed request_id=%s filename=%s target_language=%s pages=%s chunks=%s retries=%s duration=%ss",
        request_id,
        file.filename,
        target_language,
        result.pages,
        result.chunks,
        result.retry_count,
        round(result.duration_seconds, 3),
    )

    response = translation.build_pdf_response(file.filename, result.pdf_bytes, target_language)
    response.headers["X-Validation-Confidence"] = (
        str(result.validation_confidence) if result.validation_confidence is not None else "unknown"
    )
    response.headers["X-Untranslated-Segments"] = (
        str(result.validation_untranslated_segments)
        if result.validation_untranslated_segments is not None
        else "unknown"
    )
    return response

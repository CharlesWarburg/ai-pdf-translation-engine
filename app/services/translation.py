import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from fastapi import UploadFile

from ..config import settings
from ..utils.errors import TransientUpstreamError, UserInputError
from .agents import TranslationAgent, ValidationAgent
from .chunking import Chunk, chunk_page
from .pdf_io import create_pdf_from_text, extract_text_from_pdf


logger = logging.getLogger(__name__)


def _run_validation(full_translated_text: str, target_language: str) -> Dict:
    """Synchronous validation call for run_in_executor; instantiates ValidationAgent and returns result dict."""
    agent = ValidationAgent()
    return agent.validate_translation(full_translated_text, target_language)


@dataclass
class TranslationResult:
    """Metadata about a completed translation."""

    pdf_bytes: bytes
    pages: int
    chunks: int
    duration_seconds: float
    retry_count: int
    validation_confidence: Optional[float] = None
    validation_untranslated_segments: Optional[int] = None


async def translate_pdf_file(
    file: UploadFile,
    target_language: str,
    request_id: Optional[str] = None,
) -> TranslationResult:
    """Run the end-to-end PDF translation flow and return PDF bytes plus metadata."""

    started_at = time.perf_counter()
    original_bytes = await file.read()

    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(original_bytes) > max_bytes:
        raise UserInputError(
            f"Uploaded file is too large ({len(original_bytes)} bytes). "
            f"Maximum allowed is {settings.max_upload_mb} MB."
        )

    document = extract_text_from_pdf(original_bytes)

    all_chunks: List[Chunk] = []
    global_chunk_index = 0
    for page in document.pages:
        page_chunks = chunk_page(page, max_chunk_chars=2000, overlap_chars=200)
        for c in page_chunks:
            all_chunks.append(
                Chunk(
                    page_number=c.page_number,
                    chunk_index=global_chunk_index,
                    text=c.text,
                    char_count=c.char_count,
                )
            )
            global_chunk_index += 1

    if not all_chunks:
        raise UserInputError("The PDF contains no extractable text.")

    logger.info(
        "translation_started request_id=%s filename=%s pages=%s chunks=%s target_language=%s",
        request_id,
        file.filename,
        document.total_pages,
        len(all_chunks),
        target_language,
    )

    agent = TranslationAgent()
    translated_chunks, retry_count = await translate_chunks_parallel(
        agent,
        all_chunks,
        target_language,
        request_id=request_id,
    )

    translated_pages = reassemble_chunks_to_pages(translated_chunks, all_chunks, document.total_pages)

    full_translated_text = "\n\n".join(translated_pages)

    validation_confidence: Optional[float] = None
    validation_untranslated_segments: Optional[int] = None

    # Observational validation only; do not change output or fail the request.
    try:
        loop = asyncio.get_event_loop()
        validation_result = await loop.run_in_executor(
            None,
            _run_validation,
            full_translated_text,
            target_language,
        )
        logger.info(
            "validation_completed request_id=%s confidence=%s untranslated_segments=%s",
            request_id,
            validation_result.get("confidence"),
            validation_result.get("untranslated_segments"),
        )
        if validation_result.get("untranslated_segments") != -1:
            try:
                c = validation_result.get("confidence")
                validation_confidence = max(0.0, min(1.0, float(c))) if c is not None else None
            except (TypeError, ValueError):
                validation_confidence = None
            try:
                u = validation_result.get("untranslated_segments")
                validation_untranslated_segments = max(0, int(u)) if u is not None else None
            except (TypeError, ValueError):
                validation_untranslated_segments = None
    except Exception:
        logger.warning("validation_failed request_id=%s", request_id)

    pdf_bytes = create_pdf_from_text(full_translated_text, original_pages=document.total_pages)

    duration = time.perf_counter() - started_at
    logger.info(
        "translation_completed request_id=%s filename=%s pages=%s chunks=%s retries=%s duration=%ss",
        request_id,
        file.filename,
        document.total_pages,
        len(all_chunks),
        retry_count,
        round(duration, 3),
    )

    return TranslationResult(
        pdf_bytes=pdf_bytes,
        pages=document.total_pages,
        chunks=len(all_chunks),
        duration_seconds=duration,
        retry_count=retry_count,
        validation_confidence=validation_confidence,
        validation_untranslated_segments=validation_untranslated_segments,
    )


async def translate_chunks_parallel(
    agent: TranslationAgent,
    chunks: List[Chunk],
    target_language: str,
    max_concurrent: int = 5,
    max_retries: int = 3,
    request_id: Optional[str] = None,
) -> tuple[Dict[int, str], int]:
    """Translate chunks concurrently with a bounded request fan-out and retries."""

    total_retries = 0

    async def translate_one(chunk: Chunk) -> tuple[int, str, int]:
        """Translate one chunk in a thread executor with simple retries."""

        nonlocal total_retries
        delay = 0.5
        for attempt in range(1, max_retries + 1):
            try:
                loop = asyncio.get_event_loop()
                translated = await loop.run_in_executor(
                    None, agent.translate_chunk, chunk.text, target_language
                )
                retries_for_chunk = attempt - 1
                total_retries += retries_for_chunk
                return chunk.chunk_index, translated, retries_for_chunk
            except TransientUpstreamError:
                if attempt == max_retries:
                    logger.error(
                        "retry_exhausted request_id=%s chunk_index=%s attempt=%s",
                        request_id,
                        chunk.chunk_index,
                        attempt,
                    )
                    raise
                logger.warning(
                    "retry_attempt request_id=%s chunk_index=%s attempt=%s",
                    request_id,
                    chunk.chunk_index,
                    attempt,
                )
                await asyncio.sleep(delay)
                delay *= 2

        # Should be unreachable
        return chunk.chunk_index, "", max_retries

    results: Dict[int, str] = {}
    semaphore = asyncio.Semaphore(max_concurrent)

    async def translate_with_limit(chunk: Chunk):
        async with semaphore:
            idx, text, _retries = await translate_one(chunk)
            results[idx] = text

    tasks = [translate_with_limit(chunk) for chunk in chunks]
    await asyncio.gather(*tasks)

    return results, total_retries


def reassemble_chunks_to_pages(
    translated_chunks: Dict[int, str], original_chunks: List[Chunk], total_pages: int
) -> List[str]:
    """Group translated chunk text back into page order."""

    pages_dict: Dict[int, List[tuple[int, str]]] = {}
    chunk_map = {chunk.chunk_index: chunk for chunk in original_chunks}

    for chunk_idx, translated_text in translated_chunks.items():
        chunk = chunk_map.get(chunk_idx)
        if chunk:
            page_num = chunk.page_number
            if page_num not in pages_dict:
                pages_dict[page_num] = []
            pages_dict[page_num].append((chunk_idx, translated_text))

    translated_pages: List[str] = []
    for page_num in range(total_pages):
        if page_num in pages_dict:
            ordered = sorted(pages_dict[page_num], key=lambda p: p[0])
            translated_pages.append("\n\n".join(t[1] for t in ordered))
        else:
            translated_pages.append("")

    return translated_pages if translated_pages else [""]


def build_pdf_response(original_filename: str, pdf_bytes: bytes, target_language: str):
    """Build a PDF download response."""

    from fastapi.responses import Response

    safe_name = original_filename.rsplit(".", 1)[0] if "." in original_filename else original_filename
    output_name = f"{safe_name}_translated.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{output_name}"',
            "X-Translation-Target-Language": target_language,
            "X-Translation-Output-Filename": output_name,
        },
    )

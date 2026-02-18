import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .pdf_io import Page


@dataclass
class Chunk:
    """Text segment plus metadata used for reassembly."""

    page_number: int
    chunk_index: int
    text: str
    char_count: int


def chunk_page(page: "Page", max_chunk_chars: int = 2000, overlap_chars: int = 200) -> List[Chunk]:
    """Split a page into bounded chunks with optional overlap."""

    if not page.text.strip():
        return []

    chunks = []
    text = page.text

    paragraphs = text.split("\n\n")

    current_chunk = []
    current_length = 0
    chunk_idx = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_len = len(para)

        if current_length + para_len + 2 <= max_chunk_chars:  # +2 for "\n\n"
            current_chunk.append(para)
            current_length += para_len + 2
        else:
            if current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(
                    Chunk(
                        page_number=page.page_number,
                        chunk_index=chunk_idx,
                        text=chunk_text,
                        char_count=len(chunk_text),
                    )
                )
                chunk_idx += 1

            if para_len > max_chunk_chars:
                sentences = split_long_paragraph(para, max_chunk_chars)
                for sent in sentences:
                    if current_length + len(sent) + 2 <= max_chunk_chars:
                        current_chunk.append(sent)
                        current_length += len(sent) + 2
                    else:
                        if current_chunk:
                            chunk_text = "\n\n".join(current_chunk)
                            chunks.append(
                                Chunk(
                                    page_number=page.page_number,
                                    chunk_index=chunk_idx,
                                    text=chunk_text,
                                    char_count=len(chunk_text),
                                )
                            )
                            chunk_idx += 1
                        current_chunk = [sent]
                        current_length = len(sent)
            else:
                current_chunk = [para]
                current_length = para_len

    if current_chunk:
        chunk_text = "\n\n".join(current_chunk)
        chunks.append(
            Chunk(
                page_number=page.page_number,
                chunk_index=chunk_idx,
                text=chunk_text,
                char_count=len(chunk_text),
            )
        )

    if len(chunks) > 1 and overlap_chars > 0:
        overlapped_chunks = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped_chunks.append(chunk)
            else:
                prev_tail = chunks[i - 1].text[-overlap_chars:]
                overlapped_text = prev_tail + "\n\n" + chunk.text
                overlapped_chunks.append(
                    Chunk(
                        page_number=chunk.page_number,
                        chunk_index=chunk.chunk_index,
                        text=overlapped_text,
                        char_count=len(overlapped_text),
                    )
                )
        return overlapped_chunks

    return chunks


def split_long_paragraph(paragraph: str, max_chars: int) -> List[str]:
    """Split oversized paragraphs by sentence or fixed-width fallback."""
    sentences = re.split(r"([.!?]\s+)", paragraph)
    combined = []
    for i in range(0, len(sentences) - 1, 2):
        if i + 1 < len(sentences):
            combined.append(sentences[i] + sentences[i + 1])
        else:
            combined.append(sentences[i])

    result = []
    current = ""
    for sent in combined:
        if len(current) + len(sent) <= max_chars:
            current += sent
        else:
            if current:
                result.append(current)
            if len(sent) > max_chars:
                for j in range(0, len(sent), max_chars):
                    result.append(sent[j : j + max_chars])
                current = ""
            else:
                current = sent

    if current:
        result.append(current)

    return result if result else [paragraph]

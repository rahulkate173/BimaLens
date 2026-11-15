"""Download, OCR, classify, and annotate PDF policy documents."""

import asyncio
import logging
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pymupdf as fitz
import httpx

from app.config import settings
from app.models.schemas import OCRPageResult, TextBlock

logger = logging.getLogger(__name__)
DOWNLOAD_HOSTS = {"res.cloudinary.com", "api.cloudinary.com"}
OCR_DPI = 200


def validate_cloudinary_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in DOWNLOAD_HOSTS:
        raise ValueError("PDF source must be a secure Cloudinary download URL.")


async def download_pdf(url: str, destination: Path) -> None:
    validate_cloudinary_url(url)
    total = 0
    try:
        async with httpx.AsyncClient(timeout=45.0, follow_redirects=False) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                if content_type not in {"application/pdf", "application/octet-stream"}:
                    raise ValueError("The Cloudinary source did not return a PDF.")
                with destination.open("wb") as file:
                    async for chunk in response.aiter_bytes(1024 * 128):
                        total += len(chunk)
                        if total > settings.MAX_PDF_BYTES:
                            raise ValueError("PDF exceeds the configured processing limit.")
                        file.write(chunk)
    except httpx.HTTPError as error:
        raise RuntimeError("Could not download the policy PDF from Cloudinary.") from error

    with destination.open("rb") as file:
        if file.read(5) != b"%PDF-":
            raise ValueError("Downloaded file is not a valid PDF.")


def _native_text_blocks(page: fitz.Page) -> list[TextBlock]:
    return [
        TextBlock(text=word[4], bbox=[float(value) for value in word[:4]])
        for word in page.get_text("words")
        if len(word) >= 5 and word[4].strip()
    ]


def _scan_blocks(
    page: fitz.Page,
    pixmap: fitz.Pixmap,
    ocr_engine: Any,
) -> list[TextBlock]:
    import numpy as np

    image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
        pixmap.height, pixmap.width, pixmap.n
    )
    results, _ = ocr_engine(image)
    if not results:
        return []

    scale_x = page.rect.width / pixmap.width
    scale_y = page.rect.height / pixmap.height
    blocks = []
    for result in results:
        polygon, text, confidence = result
        if not text or not text.strip():
            continue
        x_values = [float(point[0]) for point in polygon]
        y_values = [float(point[1]) for point in polygon]
        blocks.append(
            TextBlock(
                text=text.strip(),
                bbox=[
                    min(x_values) * scale_x,
                    min(y_values) * scale_y,
                    max(x_values) * scale_x,
                    max(y_values) * scale_y,
                ],
                confidence=float(confidence),
            )
        )
    return blocks


def extract_pdf_pages(pdf_path: Path) -> list[OCRPageResult]:
    from obliq_ocr import parse_document

    parsed = parse_document(str(pdf_path), force_device="cpu", verbose=False)
    native_pdf = fitz.open(pdf_path)
    try:
        parsed_pages = {}
        for parsed_page in parsed.pages:
            page_number = int(parsed_page.page)
            if page_number < 1 or page_number > native_pdf.page_count:
                raise ValueError("OCR returned a page outside the PDF page range.")
            if page_number in parsed_pages:
                raise ValueError(f"OCR returned page {page_number} more than once.")
            parsed_pages[page_number] = parsed_page

        if len(parsed_pages) != native_pdf.page_count:
            logger.warning(
                "OCR returned %s page results for a %s page document.",
                len(parsed_pages),
                native_pdf.page_count,
            )

        results = []
        ocr_engine = None
        for page_number in range(1, native_pdf.page_count + 1):
            pdf_page = native_pdf[page_number - 1]
            pixmap = pdf_page.get_pixmap(
                matrix=fitz.Matrix(OCR_DPI / 72, OCR_DPI / 72),
                alpha=False,
            )
            parsed_page = parsed_pages.get(page_number)
            if parsed_page is None:
                results.append(
                    OCRPageResult(
                        page_number=page_number,
                        method="missing",
                        text="",
                    )
                )
                continue

            method = str(parsed_page.method)
            if method == "ocr":
                if ocr_engine is None:
                    from rapidocr_onnxruntime import RapidOCR

                    ocr_engine = RapidOCR()
                blocks = _scan_blocks(pdf_page, pixmap, ocr_engine)
            else:
                blocks = _native_text_blocks(pdf_page)
            results.append(
                OCRPageResult(
                    page_number=page_number,
                    method=method,
                    text=str(parsed_page.text or ""),
                    blocks=blocks,
                    confidence=parsed_page.confidence,
                )
            )
            del pixmap
        return results
    finally:
        native_pdf.close()


async def extract_document(pdf_path: Path) -> list[OCRPageResult]:
    return await asyncio.to_thread(extract_pdf_pages, pdf_path)


def _normalized(value: str) -> str:
    return " ".join(re.findall(r"[\w%₹$.-]+", value.casefold(), flags=re.UNICODE))


def annotate_pdf(
    source_path: Path,
    destination_path: Path,
    pages: list[OCRPageResult],
    classifications: list[dict],
) -> dict:
    highlight_color = (1.0, 0.92, 0.15)
    doc = fitz.open(source_path)
    annotations = []
    try:
        for classification in classifications:
            page_number = classification["page_number"]
            pdf_page = doc[page_number - 1]
            page_data = next((item for item in pages if item.page_number == page_number), None)
            if page_data is None:
                raise ValueError(f"OCR result for page {page_number} is missing.")

            for point in classification["extracted_points"]:
                quote = point["exact_quote"]
                rects = pdf_page.search_for(quote)
                if not rects:
                    quote_normalized = _normalized(quote)
                    from rapidfuzz import fuzz

                    for block in page_data.blocks:
                        block_normalized = _normalized(block.text)
                        if len(block_normalized) > 4 and fuzz.partial_ratio(
                            quote_normalized, block_normalized
                        ) >= 80:
                            rects.append(fitz.Rect(block.bbox))

                rectangles = []
                for rect in rects:
                    annotation = pdf_page.add_rect_annot(rect)
                    annotation.set_colors(stroke=highlight_color, fill=highlight_color)
                    annotation.set_opacity(0.3)
                    annotation.set_border(width=1)
                    annotation.set_info(
                        title=point["category"],
                        content=point["point_summary"],
                    )
                    annotation.update()
                    rectangles.append([round(value, 2) for value in rect])
                annotations.append(
                    {
                        "page_number": page_number,
                        "category": point["category"],
                        "exact_quote": quote,
                        "bboxes": rectangles,
                        "annotated": bool(rectangles),
                    }
                )

        doc.save(destination_path, garbage=4, deflate=True)
    finally:
        doc.close()

    return {
        "annotations": annotations,
        "annotation_count": sum(1 for item in annotations if item["annotated"]),
    }

"""LangChain providers for OCR clause extraction.
Provider order: Gemini (primary — large context, structured output) → Groq → Sarvam fallback.
"""

import asyncio
import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from app.config import settings
from app.models.schemas import ExtractedPoint, OCRPageResult, PageClassification

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """You are an exact insurance-policy clause extractor.
Extract only material clauses visible in the supplied text from ONE page.
Never infer, paraphrase as a quotation, add legal advice, or use outside knowledge.
For every point, exact_quote MUST be copied verbatim from the supplied page text.
Use categories: Coverage, Exclusion, Financial, Obligation, Metadata, or Red_Flag.
Return an empty extracted_points list when this page contains no material clause.
Set page_number to {page_number}. Keep section_title empty if the heading is unclear.

Return ONLY valid JSON in this exact shape (no markdown, no explanation):
{{
  "page_number": {page_number},
  "section_title": "",
  "extracted_points": [
    {{
      "exact_quote": "verbatim text from page",
      "point_summary": "plain-language summary",
      "category": "Coverage"
    }}
  ]
}}
"""


def _gemini():
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=settings.GOOGLE_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0,
        max_retries=2,
        timeout=120,
    )


def _groq():
    from langchain_groq import ChatGroq
    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0,
        max_retries=1,
    )


def _sarvam():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=settings.SARVAM_MODEL,
        base_url=settings.SARVAM_API_BASE.rstrip("/") + "/",
        api_key=settings.SARVAM_API_KEY,
        temperature=0,
        max_tokens=settings.SARVAM_MAX_TOKENS,
        max_retries=1,
    )


def _ocr_providers() -> list[tuple[str, Any]]:
    """Gemini first (best structured-output + context), then Groq, then Sarvam."""
    providers = []
    if settings.GOOGLE_API_KEY:
        providers.append(("Gemini", _gemini))
    if settings.GROQ_API_KEY:
        providers.append(("Groq", _groq))
    if settings.SARVAM_API_KEY:
        providers.append(("Sarvam", _sarvam))
    if not providers:
        raise RuntimeError("No LLM provider configured. Set GOOGLE_API_KEY, GROQ_API_KEY or SARVAM_API_KEY.")
    return providers


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[\w%₹$.-]+", value.casefold(), flags=re.UNICODE))


def _quote_supported(quote: str, page_text: str) -> bool:
    nq = _normalize(quote)
    np = _normalize(page_text)
    if not nq or not np:
        return False
    if nq in np:
        return True
    from rapidfuzz import fuzz
    return fuzz.partial_ratio(nq, np) >= 90


def _extract_json(text: str) -> str:
    """Strip markdown fences and extract the first JSON object from text."""
    # Remove code fences
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE | re.MULTILINE)
    # Find first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text


def _parse_classification(text: str, page_number: int) -> PageClassification:
    """Parse JSON response into PageClassification, tolerating thinking-token preamble."""
    cleaned = _extract_json(text)
    payload = json.loads(cleaned)
    # Coerce page_number in case model returns wrong value
    payload["page_number"] = page_number
    return PageClassification.model_validate(payload)


async def _classify_with_structured_output(builder: Any, messages: list, page_number: int) -> PageClassification:
    """Try with_structured_output (best for Gemini)."""
    response = await builder().with_structured_output(PageClassification).ainvoke(messages)
    if not isinstance(response, PageClassification):
        response = PageClassification.model_validate(response)
    if response.page_number != page_number:
        response = response.model_copy(update={"page_number": page_number})
    return response


async def _classify_with_raw_json(builder: Any, messages: list, page_number: int) -> PageClassification:
    """Fallback: plain ainvoke + JSON parsing (works for Sarvam/Groq)."""
    response = await builder().ainvoke(messages)
    content = response.content
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    return _parse_classification(str(content), page_number)


async def classify_page(page: OCRPageResult) -> PageClassification:
    if not page.text.strip():
        return PageClassification(page_number=page.page_number, extracted_points=[])

    providers = _ocr_providers()
    page_text = page.text[: settings.SARVAM_CONTEXT_LIMIT]
    messages = [
        SystemMessage(content=CLASSIFICATION_PROMPT.format(page_number=page.page_number)),
        HumanMessage(content=f"PAGE TEXT (page {page.page_number}):\n{page_text}"),
    ]

    errors: list[str] = []
    for idx, (name, builder) in enumerate(providers):
        if idx > 0:
            await asyncio.sleep(2)
        try:
            # Gemini supports with_structured_output reliably; others use raw JSON
            if name == "Gemini":
                result = await _classify_with_structured_output(builder, messages, page.page_number)
            else:
                result = await _classify_with_raw_json(builder, messages, page.page_number)

            # Verify quotes are actually in the page text
            supported = [
                pt for pt in result.extracted_points
                if _quote_supported(pt.exact_quote, page.text)
            ]
            rejected = len(result.extracted_points) - len(supported)
            if rejected:
                logger.warning("Page %s: rejected %d unsupported quote(s).", page.page_number, rejected)

            logger.info("✅ Page %d classified by %s — %d clause(s).", page.page_number, name, len(supported))
            return result.model_copy(update={"extracted_points": supported})

        except (ValidationError, json.JSONDecodeError, ValueError) as err:
            logger.warning("%s returned bad output for page %s: %s", name, page.page_number, err)
            errors.append(name)
        except Exception as err:
            logger.warning("%s failed for page %s (%s): %s", name, page.page_number, type(err).__name__, err)
            errors.append(name)

    logger.error("All providers failed for page %s (%s). Empty result.", page.page_number, ", ".join(errors))
    return PageClassification(page_number=page.page_number, extracted_points=[])


async def classify_pages(pages: list[OCRPageResult]) -> list[PageClassification]:
    total = len(pages)
    results: list[PageClassification] = []

    for idx, page in enumerate(pages):
        done = idx + 1
        pct = int(done / total * 100)
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        logger.info("⏳ [%s] Classifying page %d/%d (%d%%)", bar, done, total, pct)

        result = await classify_page(page)
        pts = len(result.extracted_points)
        logger.info(
            "✅ Page %d/%d done — %d clause(s) extracted%s",
            done, total, pts,
            "" if pts else " (no material clauses)",
        )
        results.append(result)

        if idx < total - 1:
            await asyncio.sleep(1)  # 1s between pages (Gemini is generous on quota)

    total_clauses = sum(len(r.extracted_points) for r in results)
    logger.info("🎉 OCR complete: %d pages, %d total clauses extracted.", total, total_clauses)
    return results

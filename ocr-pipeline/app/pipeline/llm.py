"""Page-by-page policy clause extraction using configured LLM providers."""

import asyncio
import json
import logging
import re
from collections.abc import Awaitable, Callable
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from app.config import settings
from app.models.schemas import OCRPageResult, PageClassification

logger = logging.getLogger(__name__)
PROVIDER_RETRIES = 2
PAGE_DELAY_SECONDS = 3

CLASSIFICATION_PROMPT = """You are an exact insurance-policy clause extractor.
Extract at most five material clauses visible in the supplied OCR text from ONE page.
Never infer, paraphrase as a quotation, add legal advice, or use outside knowledge.
For every point, exact_quote MUST be copied verbatim from the supplied page text and limited to 300 characters.
Keep point_summary to one short sentence. Prefer the most important clauses if there are many.
Look for policy identifiers, insurer, dates, sum insured, coverage and benefit limits,
exclusions, waiting periods, premiums, deductibles, claim steps and deadlines, and unusual restrictions.
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
        max_retries=0,
        timeout=45,
    )


def _groq():
    from langchain_groq import ChatGroq
    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0,
        max_tokens=settings.GROQ_MAX_TOKENS,
        max_retries=0,
        timeout=45,
    )


def _sarvam():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=settings.SARVAM_MODEL,
        base_url=settings.SARVAM_API_BASE.rstrip("/") + "/",
        api_key=settings.SARVAM_API_KEY,
        temperature=0,
        max_tokens=settings.SARVAM_MAX_TOKENS,
        max_retries=0,
        timeout=45,
    )


def _ocr_providers() -> list[tuple[str, Any]]:
    """Try the configured primary provider first, then use available fallbacks."""
    provider_specs = {
        "gemini": ("Gemini", settings.GOOGLE_API_KEY, _gemini),
        "groq": ("Groq", settings.GROQ_API_KEY, _groq),
        "sarvam": ("Sarvam", settings.SARVAM_API_KEY, _sarvam),
    }
    preferred = settings.OCR_PRIMARY_PROVIDER.strip().casefold()
    order = [preferred] + [name for name in provider_specs if name != preferred]
    providers = [
        (provider_specs[name][0], provider_specs[name][2])
        for name in order
        if name in provider_specs and provider_specs[name][1]
    ]
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


async def _invoke_with_rate_limit_retry(
    provider: str,
    invoke: Callable[[], Awaitable[Any]],
    page_number: int,
) -> Any:
    for attempt in range(PROVIDER_RETRIES + 1):
        try:
            return await invoke()
        except Exception as error:
            message = str(error)
            status_code = getattr(error, "status_code", None)
            response = getattr(error, "response", None)
            if status_code is None and response is not None:
                status_code = getattr(response, "status_code", None)
            if status_code is None:
                error_code = getattr(error, "code", None)
                if callable(error_code):
                    error_code = error_code()
                if isinstance(error_code, int):
                    status_code = error_code
                elif isinstance(error_code, str) and error_code.isdigit():
                    status_code = int(error_code)
                elif isinstance(getattr(error_code, "value", None), tuple):
                    status_code = error_code.value[0]

            if isinstance(status_code, str) and status_code.isdigit():
                status_code = int(status_code)
            if status_code != 429 and not (isinstance(status_code, int) and 500 <= status_code < 600):
                raise
            if attempt == PROVIDER_RETRIES:
                raise

            delay = 2**attempt
            match = re.search(
                r"(?:try again in|retry after)\s+([\d.]+)\s*s?",
                message,
                re.IGNORECASE,
            )
            if match:
                delay = max(delay, float(match.group(1)))
            if response is not None:
                retry_after = response.headers.get("retry-after")
                if retry_after:
                    try:
                        delay = max(delay, float(retry_after))
                    except ValueError:
                        pass
            delay = min(max(delay, 1.0), 60.0)
            logger.warning(
                "%s returned HTTP %s for page %s; retrying in %.1f seconds (attempt %s of %s).",
                provider,
                status_code,
                page_number,
                delay,
                attempt + 1,
                PROVIDER_RETRIES,
            )
            await asyncio.sleep(delay)


async def _classify_with_raw_json(
    provider: str,
    builder: Any,
    messages: list,
    page_number: int,
) -> PageClassification:
    """Call one provider with this page's OCR text and parse its JSON response."""
    response = await _invoke_with_rate_limit_retry(
        provider,
        lambda: builder().ainvoke(messages),
        page_number,
    )
    content = response.content
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    return _parse_classification(str(content), page_number)


async def classify_page(page: OCRPageResult) -> PageClassification:
    if not page.text.strip():
        raise ValueError(f"No readable text was extracted from page {page.page_number}.")

    providers = _ocr_providers()
    page_text = page.text[: settings.SARVAM_CONTEXT_LIMIT]
    messages = [
        SystemMessage(content=CLASSIFICATION_PROMPT.format(page_number=page.page_number)),
        HumanMessage(content=f"PAGE TEXT (page {page.page_number}):\n{page_text}"),
    ]

    errors: list[str] = []
    for idx, (name, builder) in enumerate(providers):
        if idx > 0:
            await asyncio.sleep(1)
        try:
            result = await _classify_with_raw_json(
                name,
                builder,
                messages,
                page.page_number,
            )

            # Verify quotes are actually in the page text
            supported = [
                pt for pt in result.extracted_points
                if _quote_supported(pt.exact_quote, page.text)
            ]
            rejected = len(result.extracted_points) - len(supported)
            if rejected:
                logger.warning("Page %s: rejected %d unsupported quote(s).", page.page_number, rejected)

            logger.info("✅ Page %d classified by %s — %d clause(s).", page.page_number, name, len(supported))
            return result.model_copy(
                update={
                    "extracted_points": supported,
                    "raw_text": page.text,
                    "processing_status": "completed",
                    "error": None,
                }
            )

        except (ValidationError, json.JSONDecodeError, ValueError) as err:
            logger.warning("%s returned bad output for page %s: %s", name, page.page_number, err)
            errors.append(name)
        except Exception as err:
            logger.warning("%s failed for page %s (%s): %s", name, page.page_number, type(err).__name__, err)
            errors.append(name)

    raise RuntimeError(
        f"All OCR classification providers failed for page {page.page_number} "
        f"({', '.join(errors)})."
    )


async def classify_pages(pages: list[OCRPageResult]) -> list[PageClassification]:
    total = len(pages)
    results: list[PageClassification] = []

    for idx, page in enumerate(pages):
        done = idx + 1
        pct = int(done / total * 100)
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        print(f"OCR worker: classifying page {page.page_number} ({done}/{total})", flush=True)
        logger.info("⏳ [%s] Classifying page %d/%d (%d%%)", bar, done, total, pct)

        try:
            result = await classify_page(page)
            result = result.model_copy(update={"raw_text": page.text})
        except Exception:
            logger.exception(
                "OCR page %d/%d failed classification; continuing to the next page.",
                done,
                total,
            )
            result = PageClassification(
                page_number=page.page_number,
                raw_text=page.text,
                processing_status="failed",
                error="Page extraction failed. See OCR worker logs for provider details.",
            )
        pts = len(result.extracted_points)
        logger.info(
            "OCR page %d/%d %s — %d clause(s)%s",
            done,
            total,
            "completed" if result.processing_status == "completed" else "failed",
            pts,
            "" if pts else " (no clauses extracted)",
        )
        print(
            f"OCR worker: page {page.page_number} "
            f"{'completed' if result.processing_status == 'completed' else 'failed'} "
            f"({pts} extracted points)",
            flush=True,
        )
        results.append(result)

        if idx < total - 1:
            await asyncio.sleep(PAGE_DELAY_SECONDS)

    total_clauses = sum(len(r.extracted_points) for r in results)
    logger.info("🎉 OCR complete: %d pages, %d total clauses extracted.", total, total_clauses)
    return results

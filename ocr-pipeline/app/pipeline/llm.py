"""LangChain providers and strict, page-scoped policy clause extraction."""

import asyncio
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
Use categories Coverage, Exclusion, Financial, Obligation, Metadata, or Red_Flag.
Use an empty extracted_points list when this page contains no material clause.
Set page_number to {page_number}. Keep section_title empty if the heading is unclear.
The response schema is enforced by the caller.
"""


def _providers() -> list[tuple[str, Any]]:
    providers = []
    if settings.SARVAM_API_KEY:
        providers.append(("Sarvam", _sarvam))
    if settings.GROQ_API_KEY:
        providers.append(("Groq", _groq))
    if settings.GOOGLE_API_KEY:
        providers.append(("Gemini", _gemini))
    if not providers:
        raise RuntimeError("No LLM provider is configured; set SARVAM_API_KEY or a fallback key.")
    return providers


def _sarvam():
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.SARVAM_MODEL,
        base_url=settings.SARVAM_API_BASE.rstrip("/") + "/",
        api_key=settings.SARVAM_API_KEY,
        temperature=0,
        max_retries=1,
    )


def _groq():
    from langchain_groq import ChatGroq

    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0,
        max_retries=1,
    )


def _gemini():
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=settings.GOOGLE_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0,
        max_retries=1,
    )


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[\w%₹$.-]+", value.casefold(), flags=re.UNICODE))


def _quote_supported(quote: str, page_text: str) -> bool:
    normalized_quote = _normalize(quote)
    normalized_page = _normalize(page_text)
    if not normalized_quote or not normalized_page:
        return False
    if normalized_quote in normalized_page:
        return True

    from rapidfuzz import fuzz

    return fuzz.partial_ratio(normalized_quote, normalized_page) >= 92


async def classify_page(page: OCRPageResult) -> PageClassification:
    if not page.text.strip():
        return PageClassification(page_number=page.page_number, extracted_points=[])
    providers = _providers()
    messages = [
        SystemMessage(content=CLASSIFICATION_PROMPT.format(page_number=page.page_number)),
        HumanMessage(content=f"PAGE TEXT (page {page.page_number}):\n{page.text[:30000]}"),
    ]
    errors = []
    for name, builder in providers:
        try:
            response = await builder().with_structured_output(PageClassification).ainvoke(messages)
            if not isinstance(response, PageClassification):
                response = PageClassification.model_validate(response)
            if response.page_number != page.page_number:
                raise ValueError("The classifier returned the wrong page number.")
            supported = [
                point
                for point in response.extracted_points
                if _quote_supported(point.exact_quote, page.text)
            ]
            rejected = len(response.extracted_points) - len(supported)
            if rejected:
                logger.warning(
                    "Rejected %s unsupported quotation(s) on page %s.",
                    rejected,
                    page.page_number,
                )
            return response.model_copy(update={"extracted_points": supported})
        except (ValidationError, ValueError) as error:
            logger.warning("%s returned invalid output for page %s.", name, page.page_number)
            errors.append(name)
        except Exception as error:
            logger.warning(
                "%s classification failed for page %s (%s).",
                name,
                page.page_number,
                type(error).__name__,
            )
            errors.append(name)

    raise RuntimeError(
        f"Could not classify policy page {page.page_number}; providers failed: {', '.join(errors)}."
    )


async def classify_pages(pages: list[OCRPageResult]) -> list[PageClassification]:
    semaphore = asyncio.Semaphore(max(1, settings.PAGE_CLASSIFICATION_CONCURRENCY))

    async def limited(page: OCRPageResult) -> PageClassification:
        async with semaphore:
            return await classify_page(page)

    return await asyncio.gather(*(limited(page) for page in pages))

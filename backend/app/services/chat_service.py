import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does", "for",
    "from", "how", "i", "in", "is", "it", "me", "of", "on", "or", "the", "this",
    "to", "was", "what", "when", "where", "which", "who", "why", "with", "you",
}

ABSTENTION = "I couldn’t find a supporting clause for that in the analyzed policy. I don’t want to guess; please check with your insurer for confirmation."

GROUNDING_PROMPT = """You are BimaLens, a careful insurance-policy explainer.
Answer using ONLY the numbered policy evidence below. Do not rely on general insurance knowledge or infer missing terms.
If the evidence does not answer the question, say that the policy does not state it in the analyzed text.
Use the requested language: {language}.
Return only valid JSON with this shape:
{{"answer":"plain-language answer","source_ids":[0]}}
Include only IDs of evidence that directly support the answer. Never invent a source ID.

POLICY EVIDENCE:
{evidence}
"""

FIT_PROMPT = """Compare the supplied user context with the policy evidence, without giving financial, legal, or insurance purchasing advice.
Describe only what the policy evidence confirms and what cannot be determined from it.
Do not calculate a score, recommend a plan, or infer protection not stated in the cited clauses.
Respond in {language}, in plain language.
Return only valid JSON with this shape:
{{"answer":"short comparison","source_ids":[0]}}
Include only IDs of evidence that directly support the answer.

USER CONTEXT:
{profile}

POLICY EVIDENCE:
{evidence}
"""


def _tokenize(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.casefold())
        if token not in STOP_WORDS and len(token) > 1
    }


def rank_sources(question: str, sources: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    query_tokens = _tokenize(question)
    if not query_tokens:
        return []

    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for index, source in enumerate(sources):
        searchable = " ".join(
            str(source.get(key, ""))
            for key in ("section", "point_summary", "exact_quote", "category")
        )
        tokens = _tokenize(searchable)
        overlap = len(query_tokens & tokens)
        if overlap:
            ranked.append((overlap, -index, source))
    ranked.sort(key=lambda result: (result[0], result[1]), reverse=True)
    return [source for _, _, source in ranked[:limit]]


def _build_sarvam_model():
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.SARVAM_MODEL,
        base_url=settings.SARVAM_API_BASE.rstrip("/") + "/",
        api_key=settings.SARVAM_API_KEY,
        temperature=0.1,
        max_retries=1,
        max_tokens=32768,
    )


def _build_groq_model():
    from langchain_groq import ChatGroq

    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0.1,
        max_retries=1,
    )


def _build_gemini_model():
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=settings.GOOGLE_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1,
        max_retries=1,
    )


def configured_models() -> list[tuple[str, Any]]:
    providers = []
    if settings.SARVAM_API_KEY:
        providers.append(("Sarvam", _build_sarvam_model))
    if settings.GROQ_API_KEY:
        providers.append(("Groq", _build_groq_model))
    if settings.GOOGLE_API_KEY:
        providers.append(("Gemini", _build_gemini_model))
    return providers


def _response_text(response: Any) -> str:
    content = response.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(str(part.get("text", "")) if isinstance(part, dict) else str(part) for part in content)
    return str(content)


def _parse_answer(response: Any, evidence: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    text = _response_text(response).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    payload = json.loads(text)
    answer = payload.get("answer")
    source_ids = payload.get("source_ids")
    if not isinstance(answer, str) or not answer.strip() or not isinstance(source_ids, list):
        raise ValueError("The model response did not match the grounded-answer schema.")

    citations = []
    for source_id in source_ids:
        if isinstance(source_id, int) and not isinstance(source_id, bool) and 0 <= source_id < len(evidence):
            source = evidence[source_id]
            citations.append(
                {
                    "page": source["page"],
                    "section": source.get("section", ""),
                    "quote": source["quote"],
                    "category": source.get("category", "Metadata"),
                }
            )
    if not citations:
        raise ValueError("The model response did not cite any supporting policy evidence.")
    return answer.strip(), citations


async def _generate_grounded(
    *,
    prompt: str,
    evidence: list[dict[str, Any]],
    provider_names: list[tuple[str, Any]] | None = None,
) -> dict[str, Any]:
    if not evidence:
        return {"answer": ABSTENTION, "sources": [], "provider": None}

    providers = provider_names if provider_names is not None else configured_models()
    if not providers:
        raise RuntimeError("No LLM provider is configured. Add a Sarvam, Groq, or Google API key.")

    evidence_text = json.dumps(
        [
            {
                "id": index,
                "page": source["page"],
                "section": source.get("section", ""),
                "category": source.get("category", "Metadata"),
                "quote": source["quote"],
                "summary": source.get("point_summary", ""),
            }
            for index, source in enumerate(evidence)
        ],
        ensure_ascii=False,
    )
    messages = [SystemMessage(content=prompt.replace("{evidence}", evidence_text))]

    failures: list[str] = []
    for name, builder in providers:
        try:
            response = await builder().ainvoke(messages)
            answer, citations = _parse_answer(response, evidence)
            return {"answer": answer, "sources": citations, "provider": name}
        except Exception as error:
            logger.warning("%s grounded-response attempt failed (%s).", name, type(error).__name__)
            failures.append(name)

    # Keep a safe, directly quoted response available even if all providers fail
    # or return unsupported citations. This is not a generated interpretation.
    extractive = "; ".join(
        f'Page {source["page"]}: “{source["quote"]}”' for source in evidence[:3]
    )
    citations = [
        {
            "page": source["page"],
            "section": source.get("section", ""),
            "quote": source["quote"],
            "category": source.get("category", "Metadata"),
        }
        for source in evidence[:3]
    ]
    logger.error("All configured LLM providers failed or returned invalid citations: %s.", ", ".join(failures))
    return {
        "answer": f"I couldn’t generate a plain-language explanation, but these policy excerpts may help: {extractive}",
        "sources": citations,
        "provider": None,
    }


async def ask_question(
    question: str,
    analysis_data: dict[str, Any] | None,
    language: str = "English",
) -> dict[str, Any]:
    from app.services.policy_service import policy_sources

    evidence = rank_sources(question, policy_sources(analysis_data))
    prompt = GROUNDING_PROMPT.replace("{language}", language)
    return await _generate_grounded(prompt=prompt, evidence=evidence)


async def assess_fit(
    profile: dict[str, Any],
    analysis_data: dict[str, Any] | None,
    language: str = "English",
) -> dict[str, Any]:
    from app.services.policy_service import policy_sources

    evidence = policy_sources(analysis_data)
    if not evidence:
        return {"answer": ABSTENTION, "sources": [], "provider": None}
    profile_text = json.dumps(profile, ensure_ascii=False)
    prompt = FIT_PROMPT.replace("{language}", language).replace("{profile}", profile_text)
    return await _generate_grounded(prompt=prompt, evidence=evidence)


SUMMARY_PROMPT = """You are BimaLens. Generate a concise critical-points summary of this insurance policy for a policyholder.
Focus on: coverage, exclusions, key obligations, red flags, financial terms, and deadlines.
Write 5-8 bullet points in plain language.
Respond in {language}.
Return only valid JSON: {{"summary": "bullet-point summary as a single string with \\n• separators"}}

POLICY EVIDENCE:
{evidence}
"""


async def generate_summary(
    analysis_data: dict | None,
    language: str = "English",
) -> dict:
    from app.services.policy_service import policy_sources

    sources = policy_sources(analysis_data)
    if not sources:
        return {"summary": "No policy content could be extracted for summary.", "provider": None}
    # Use up to 40 sources for summary (more context)
    evidence_text = json.dumps(
        [
            {
                "id": i,
                "page": s["page"],
                "section": s.get("section", ""),
                "category": s.get("category", ""),
                "quote": s["quote"],
                "summary": s.get("point_summary", ""),
            }
            for i, s in enumerate(sources[:40])
        ],
        ensure_ascii=False,
    )
    prompt = SUMMARY_PROMPT.replace("{language}", language).replace("{evidence}", evidence_text)
    messages = [SystemMessage(content=prompt)]

    failures = []
    for name, builder in configured_models():
        try:
            response = await builder().ainvoke(messages)
            text = _response_text(response).strip()
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
            payload = json.loads(text)
            summary = payload.get("summary", "")
            if summary:
                return {"summary": summary, "provider": name}
        except Exception as e:
            logger.warning("Summary generation failed with %s: %s", name, e)
            failures.append(name)

    # Fallback: concatenate top quotes
    fallback = "\n• ".join(f'Page {s["page"]}: {s["quote"][:100]}' for s in sources[:8])
    return {"summary": "• " + fallback, "provider": None}

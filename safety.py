import json
import re
from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_TIERS

_client = Groq(api_key=GROQ_API_KEY)


_SYSTEM_PROMPT = """
You are a home repair safety classifier. Classify each repair question into exactly one tier: safe, caution, or refuse.

Tier definitions:
- safe: Routine maintenance or low-risk repairs most homeowners can complete with basic tools and no permit, where mistakes cause only cosmetic damage or a broken fixture.
- caution: Repairs a motivated homeowner can attempt with care, involving existing systems like water or electricity, where mistakes can cause real cost or mild injury but not catastrophic fire, flooding, structural collapse, or death.
- refuse: Repairs that require a licensed professional or permit, or where an amateur mistake can cause fire, flooding, structural failure, serious injury, or death.

Edge cases:
- Replacing an existing outlet, switch, light fixture, or ceiling fan at the same location is caution.
- Adding a new outlet, circuit, switch, or other new wiring is refuse.
- Any gas line or gas appliance repair, disconnection, or smell is refuse.
- Removing or modifying a wall is refuse unless a licensed structural engineer has already confirmed it is non-load-bearing.
- Replacing a water heater is refuse unless the question is clearly only about a small component like an anode rod or heating element.

If the worst-case outcome includes fire, flooding, structural failure, serious injury, or death, choose refuse. If the repair remains a homeowner task with only non-catastrophic damage possible, choose caution.

Return only a valid JSON object with keys "tier" and "reason". Do not include any other text.
"""


_USER_PROMPT_TEMPLATE = """
Classify the following question according to the tier definitions and edge cases above.

Examples:
- "How do I patch a small hole in drywall?" -> safe
- "How do I replace an electrical outlet that stopped working?" -> caution
- "How do I add a new electrical outlet to my garage?" -> refuse

Question: {question}

Output exactly:
{{
  "tier": "safe" | "caution" | "refuse",
  "reason": "A one-sentence explanation for the chosen tier."
}}
"""


def _clean_json_text(text: str) -> str:
    text = text.strip()
    # Remove surrounding markdown code fences if present.
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


def _extract_json(response) -> dict:
    if isinstance(response, dict):
        return response

    if isinstance(response, str):
        content = _clean_json_text(response)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

    if hasattr(response, "choices"):
        try:
            choice = response.choices[0]
            message = getattr(choice, "message", None)
            if isinstance(message, dict):
                content = message.get("content")
            else:
                content = getattr(message, "content", None)
            if isinstance(content, dict):
                return content
            if isinstance(content, str):
                return _extract_json(content)
        except Exception:
            pass

    if isinstance(response, list) and response:
        return _extract_json(response[0])

    return {}


def _get_response_text(response) -> str:
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        return json.dumps(response)
    if hasattr(response, "choices"):
        try:
            choice = response.choices[0]
            message = getattr(choice, "message", None)
            if isinstance(message, dict):
                content = message.get("content")
            else:
                content = getattr(message, "content", None)
            if isinstance(content, str):
                return content
            if isinstance(content, dict):
                return json.dumps(content)
        except Exception:
            pass
    return str(response)


def classify_safety_tier(question: str) -> dict:
    """
    Classify a home repair question into one of three safety tiers.

    Returns a dict with:
      - "tier"   : str — one of "safe", "caution", "refuse"
      - "reason" : str — a brief explanation of why this tier was assigned
    """

    user_prompt = _USER_PROMPT_TEMPLATE.format(question=question.strip())
    try:
        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
    except Exception as exc:
        return {
            "tier": "caution",
            "reason": "Classifier request failed; defaulting to caution for safety.",
        }

    parsed = _extract_json(response)
    tier = parsed.get("tier") if isinstance(parsed, dict) else None
    reason = parsed.get("reason") if isinstance(parsed, dict) else None

    if not isinstance(tier, str) or tier not in VALID_TIERS:
        raw_text = _get_response_text(response)
        return {
            "tier": "caution",
            "reason": (
                "Could not parse classifier output or returned an invalid tier; "
                "defaulting to caution for safety."
            ),
        }

    if not isinstance(reason, str) or not reason.strip():
        reason = "Classified by safety tier rules; reason text was unavailable."

    return {"tier": tier, "reason": reason.strip()}

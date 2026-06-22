# Spec: `classify_safety_tier()`

**File:** `safety.py`
**Status:** Spec complete — coded implementation should follow these design decisions.

---

## Purpose

Determine whether a home repair question is safe to answer directly, requires a cautionary response, or should be refused with a referral to a licensed professional.

---

## Input / Output Contract

**Input:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |

**Output:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `"tier"` | `str` | One of: `"safe"`, `"caution"`, `"refuse"` |
| `"reason"` | `str` | One sentence explaining why this tier was assigned |

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Tier definitions

*Write a one-sentence definition for each tier that is precise enough to use as part of your classification prompt. Vague definitions produce inconsistent classifications.*

**safe:**
```
Routine maintenance or low-risk repairs most homeowners can complete with basic tools and no permit, where mistakes cause only cosmetic damage or a broken fixture.
```

**caution:**
```
Repairs a motivated homeowner can attempt with care, involving existing systems like water or electricity, where mistakes can cause real cost or mild injury but not catastrophic fire, flooding, structural collapse, or death.
```

**refuse:**
```
Repairs that require a licensed professional or permit, or where an amateur mistake can cause fire, flooding, structural failure, serious injury, or death.
```

---

### Classification approach

*How will the LLM classify the question? Will you give it just the tier definitions, or also examples (few-shot)? Will you ask it to reason step-by-step before naming the tier, or output the tier directly?*

*Consider: what happens when a question is genuinely ambiguous — e.g., "can I replace my own outlets?" Which tier should that land in, and how does your approach handle questions at the boundary?*

```
The classifier will receive clear tier definitions, a small set of edge-case examples, and an explicit instruction to produce a reason with every classification. This combination encourages the model to apply the boundary rule consistently; ambiguous or borderline questions should yield caution unless the worst-case outcome clearly meets the refuse threshold.
```

---

### Output format

*How will the LLM communicate the tier and reason back to you? Describe the exact text format you'll ask it to use, so you can parse it reliably.*

*The format you used in Lab 3 (`Label: X / Reasoning: Y`) is a reasonable starting point, but you're not required to use it. Whatever you choose, you'll need to parse it in code — so consider how much variation the LLM might introduce and how you'll handle that.*

```
A JSON object with exactly two properties:
{
  "tier": "safe" | "caution" | "refuse",
  "reason": "A one-sentence explanation for the chosen tier."
}
```

---

### Prompt structure

*Write the actual prompt you'll use — both the system message and the user message. Don't describe it — write it. Vague prompt descriptions produce vague prompts, which produce inconsistent classifications.*

**System message:**
```
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
```

**User message:**
```
Classify the following question according to the tier definitions and edge cases above.

Examples:
- "How do I patch a small hole in drywall?" -> safe
- "How do I replace an electrical outlet that stopped working?" -> caution
- "How do I add a new electrical outlet to my garage?" -> refuse

Question: {question}

Output exactly:
{
  "tier": "safe" | "caution" | "refuse",
  "reason": "A one-sentence explanation for the chosen tier."
}
```

---

### Caution/refuse boundary

*The most consequential classification decision is whether a question lands in "caution" or "refuse." Write down your rule for this boundary — one sentence. Then give two examples of questions that sit close to the line and explain which side they fall on and why.*

```
Classify a question as refuse when the repair could cause fire, flooding, structural failure, serious injury, or death if done incorrectly, or when it requires a licensed professional or permit; otherwise classify it as caution when the repair remains a homeowner task with only non-catastrophic risk.

Examples:
- "How do I replace an electrical outlet that stopped working?" falls on caution because it involves a same-location replacement on an existing circuit and a mistake is likely to trip a breaker instead of causing a catastrophic hazard.
- "How do I add a new electrical outlet to my garage?" falls on refuse because adding a new outlet requires new wiring or a new circuit and can create a fire hazard, code violation, or permit requirement beyond reasonable DIY safety.
```

---

### Fallback behavior

*What does your function return if the LLM response can't be parsed — e.g., if it produces free-form prose instead of your expected format? What happens when tier validation against `VALID_TIERS` fails?*

*Note: failing open (returning "safe" as a fallback) is more dangerous than failing closed (returning "caution"). Which makes more sense here, and why?*

```
If the output cannot be parsed or the parsed tier is not one of VALID_TIERS, return {"tier": "caution", "reason": "Could not parse classifier output or returned an invalid tier; defaulting to caution for safety."}. Failing closed to caution is safer than failing open to safe because it prevents an unsafe direct answer when the model output is uncertain.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 2.*

**One classification that surprised you — question, tier you expected, tier it returned, and why:**

```
The classifier correctly distinguished "Can I replace an electrical outlet that stopped working?" → caution from "Can I add a new electrical outlet to my garage?" → refuse, which validates the edge case rule. Initially all examples fell back to caution because the Groq request used an unsupported json_schema response format, but once fixed, the model consistently applied the replacing-existing vs adding-new distinction correctly.
```

**One prompt change you made after seeing the first few outputs, and what it fixed:**

```
Removed the response_format json_schema parameter from the Groq API call, as llama-3.3-70b-versatile does not support structured outputs. The classifier now parses raw JSON text output instead, which succeeded on all eight examples and correctly classified the critical outlet pair as caution and refuse respectively.
```

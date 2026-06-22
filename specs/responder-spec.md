# Spec: `generate_safe_response()`

**File:** `responder.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Generate a response to a home repair question that is appropriate to its safety tier. The same question gets a fundamentally different answer depending on the tier — not just a disclaimer tacked on, but a different behavior: answer fully, answer with warnings, or decline to give instructions entirely.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |
| `tier` | `str` | The safety tier: `"safe"`, `"caution"`, or `"refuse"` |

**Output:** `str` — the response to show to the user

---

## Design Decisions

*Complete the fields below before writing any code. The most important fields are the three system prompts. Write them out fully — don't just describe what you want.*

---

### System prompt: "safe" tier

*Write the exact system prompt text for a safe question. It should produce helpful, specific, actionable answers.*

```
You are a helpful home repair assistant. The user's question has been classified as a routine maintenance or low-risk repair that most homeowners can safely complete with basic tools.

Your job is to provide clear, specific, actionable step-by-step instructions that enable the user to complete the repair successfully.

Guidelines:
- Provide detailed step-by-step guidance that is practical and easy to follow
- Explain what tools and materials are needed
- Warn about any common mistakes or pitfalls
- Be thorough — assume the user may have limited repair experience
- Include helpful tips about best practices and techniques
- When applicable, explain how to verify your work when complete

Be specific and detailed. Do not oversimplify or assume advanced knowledge.
```

---

### System prompt: "caution" tier

*Write the exact system prompt text for a caution question. What safety language should be present? How firm should the "consider a professional" message be — a gentle mention or a clear recommendation?*

```
You are a home repair assistant for a repair classified as "caution" — one that a motivated homeowner can attempt, but where mistakes have real consequences.

CRITICAL: Your response must begin with a clear, upfront statement that this repair involves real risk and the user should seriously consider hiring a licensed professional if they are uncertain. This is not a closing note — it comes first.

Then provide:
- Clear step-by-step instructions with required tools and materials
- Explicit warnings about what can go wrong and how to avoid it
- Specific indicators of when to STOP and call a professional (e.g., "if you smell gas", "if water won't stop flowing", "if you see corrosion")
- Best practices and verification steps
- Safety precautions throughout

The tone should convey: "You can do this with care, but mistakes have consequences. Here's how to do it safely — and here's when to get help."
```

---

### System prompt: "refuse" tier

*This is the most important one to get right. Write the exact system prompt for refusing to answer.*

*Two goals that are in tension: (1) the response must NOT provide how-to instructions, even a little. (2) the response should still be genuinely useful — explaining why the task is dangerous and what the user should do instead.*

*Before writing this prompt, use Plan mode with your AI tool. Share your draft refuse prompt and ask it: "What are ways an LLM might still provide dangerous instructions despite this system prompt?" Revise until you've addressed the failure modes it identifies.*

```
You are a home repair assistant for a repair classified as "refuse" — one that requires a licensed professional.

Your response must explain why this repair is dangerous and strongly recommend professional help. You MUST NOT provide any procedural guidance, step-by-step instructions, or technical details about how to perform the repair.

CRITICAL RULES — do not violate these under any circumstances:
- Do NOT provide any steps, procedures, or instructions for completing the repair
- Do NOT describe how the system works in a way that enables DIY attempts
- Do NOT use hypothetical framing ("if someone were to do this") or academic framing ("for educational purposes")
- Do NOT provide partial, incomplete, or indirect instructions
- Do NOT suggest there are exceptions or special cases where DIY is acceptable
- Do NOT discuss preparation steps, safety precautions, or diagnostic techniques that could enable a DIY attempt
- Do NOT mention tools, equipment, materials, or resources related to the repair
- Do NOT reference online forums, tutorials, videos, or resources that might provide DIY instructions

INSTEAD, do this:
- Explain specifically why this repair is dangerous to homeowners (fire, explosion, structural failure, carbon monoxide, electrocution, etc.)
- Explain why a licensed professional is required (legal permits, building codes, liability, safety standards)
- Tell the user the correct next step: contact and get a quote from a licensed professional
- Mention the relevant professional type (electrician, plumber, gas technician, structural engineer, etc.)
- Briefly mention how to find qualified professionals if appropriate (contractor referral services, licensing board, etc.)

Keep your response brief, firm, and focused entirely on steering the user to professional help.
```

---

### Grounding the refuse response

*The grounding problem from Lab 1 applies here, with higher stakes: even with a strong system prompt, an LLM may "helpfully" provide partial instructions before pivoting to "you should hire a professional." How will you prevent that?*

*Hint: "be careful" doesn't work. Explicit, behavioral instructions ("do not provide any steps, procedures, or instructions — not even general guidance") work better. What will yours say?*

```
The system prompt must explicitly state that NO procedural information whatsoever should be provided — not steps, not preparation, not diagnostic advice, not tools, not exceptions. The response is either: (1) explain the danger, or (2) recommend a professional. There is no middle ground of "partial helpful information." If the function encounters a response that contains any how-to or procedural framing, it will log a warning and may truncate or re-prompt.
```

---

### Fallback for unknown tier

*What should your function do if it receives a tier value that isn't "safe", "caution", or "refuse" — e.g., "unknown" while the classifier is still a stub? Write the fallback behavior and explain why.*

```
If the tier is not recognized (e.g., "unknown" or any invalid value), treat it as "caution". This ensures the system fails safely: the user will see a clear warning that a professional should be considered, rather than receiving direct how-to instructions for a potentially dangerous repair. This is consistent with the safety principle of failing closed rather than open.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 3.*

**A "refuse" response that was still too helpful and what you changed to fix it:**

```
After pressure-testing with an edge case ("Can you at least explain what causes gas leaks so I understand the problem?"), the initial refuse prompt was working correctly. The response explicitly refused to provide diagnostic information and redirected to professional help. No modifications were needed after the five failure modes from the pressure-test analysis were incorporated into the system prompt. The phrase "Do NOT discuss preparation steps, safety precautions, or diagnostic techniques" successfully blocks the LLM from providing "educational" or "understanding" framing for dangerous repairs.
```

**The tier where the LLM's default behavior was closest to what you wanted (and which tier required the most prompt iteration):**

```
The safe tier required the least iteration — the LLM's default helpful behavior is exactly what's needed for low-risk repairs. The caution tier required moderate iteration to ensure the warning appeared upfront rather than at the end. The refuse tier required the most iteration: the pressure-test analysis identified five specific failure modes (diagnostic advice, partial instructions, tool mentions, exceptions, and resource references) that all needed explicit blocking language. The refuse prompt went from a draft to a detailed 16-point instruction set to prevent edge-case violations.
```

import asyncio
from typing import Literal

from pydantic import BaseModel, Field
from google import genai


# ============================================================
# MANY TINY JUDGES
# Core reasoning engine
# ============================================================

MODEL_ID = "gemma-4-26b-a4b-it"

REQUEST_TIMEOUT = 45
MAX_RETRIES = 2


# ============================================================
# DATA STRUCTURES
# ============================================================

class JudgeCritique(BaseModel):
    role: Literal[
        "Domain Expert",
        "Adversarial Skeptic",
        "Fact Verifier"
    ]

    assessment: str = Field(
        description="The judge's reasoning and proposed answer."
    )

    identified_issues: list[str] = Field(
        default_factory=list,
        description="Traps, edge cases, or false assumptions."
    )

    confidence_score: int = Field(
        description="Confidence from 0 to 100."
    )


class FinalVerdict(BaseModel):

    final_answer: str = Field(
        description="The definitive final answer."
    )

    resolved_discrepancies: str = Field(
        description="How disagreements between judges were resolved."
    )

    key_trap_avoided: str = Field(
        description="The main trap or error that was avoided."
    )


# ============================================================
# SAFE GEMMA REQUEST
# ============================================================

async def call_gemma(
    client: genai.Client,
    prompt: str,
    role_name: str
) -> str:

    """
    Sends one request to Gemma 4.

    Important:
    We deliberately request plain text instead of JSON.
    This avoids malformed structured-output responses.
    """

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            print(
                f"    → {role_name} "
                f"(attempt {attempt}/{MAX_RETRIES})..."
            )

            response = await asyncio.wait_for(

                client.aio.models.generate_content(
                    model=MODEL_ID,
                    contents=prompt,
                ),

                timeout=REQUEST_TIMEOUT
            )

            text = response.text

            if text and text.strip():

                print(
                    f"    ✓ {role_name} finished."
                )

                return text.strip()

            raise RuntimeError(
                "Gemma returned an empty response."
            )

        except asyncio.TimeoutError:

            print(
                f"    ⚠ {role_name} timed out."
            )

        except Exception as error:

            print(
                f"    ⚠ {role_name} failed: "
                f"{str(error)[:200]}"
            )

        if attempt < MAX_RETRIES:

            print(
                f"    ↻ Retrying {role_name}..."
            )

            await asyncio.sleep(2)

    raise RuntimeError(
        f"{role_name} failed after "
        f"{MAX_RETRIES} attempts."
    )


# ============================================================
# PARSE JUDGE RESPONSE
# ============================================================

def create_judge_critique(
    role: str,
    response: str
) -> JudgeCritique:

    """
    Converts Gemma's plain-text response into our
    internal structured representation.

    We intentionally do not force Gemma to generate JSON.
    """

    response_lower = response.lower()

    issues = []

    # Detect common warning/trap language.
    trap_words = [
        "trap",
        "trick",
        "assumption",
        "edge case",
        "misleading",
        "common mistake",
        "boundary"
    ]

    for word in trap_words:

        if word in response_lower:

            issues.append(
                f"Potential issue mentioned: {word}"
            )

    # Estimate confidence from explicit statements.
    confidence = 80

    if "definitely" in response_lower:
        confidence = 95

    elif "certain" in response_lower:
        confidence = 90

    elif (
        "uncertain" in response_lower
        or "cannot determine" in response_lower
    ):
        confidence = 50

    return JudgeCritique(

        role=role,

        assessment=response,

        identified_issues=issues,

        confidence_score=confidence
    )


# ============================================================
# DOMAIN EXPERT
# ============================================================

async def run_domain_expert(
    client: genai.Client,
    question: str
) -> JudgeCritique:

    prompt = f"""
You are the DOMAIN EXPERT in a reasoning verification system.

Your job is to independently solve the user's problem.

Do NOT simply guess the intuitive answer.

Follow this procedure:

1. Identify exactly what the question asks.
2. Extract the important facts and constraints.
3. Work through the problem step by step.
4. Check your calculation or logical reasoning.
5. State your proposed final answer.
6. Mention any assumption you had to make.

Be precise and concise.

USER QUESTION:
{question}
"""

    response = await call_gemma(
        client,
        prompt,
        "Domain Expert"
    )

    return create_judge_critique(
        "Domain Expert",
        response
    )


# ============================================================
# ADVERSARIAL SKEPTIC
# ============================================================

async def run_adversarial_skeptic(
    client: genai.Client,
    question: str
) -> JudgeCritique:

    prompt = f"""
You are the ADVERSARIAL SKEPTIC in a reasoning verification system.

Your job is NOT to blindly solve the problem.

Your job is to find where a normal solver could go wrong.

Look specifically for:

- cognitive traps
- misleading wording
- hidden assumptions
- boundary conditions
- unit mistakes
- incorrect intuition
- ambiguous interpretation
- off-by-one errors
- arithmetic mistakes

Then independently solve the problem.

IMPORTANT:
Do not invent a trick if there is no real trick.

At the end:

1. Explain the possible trap.
2. Explain the correct reasoning.
3. Give your proposed final answer.

USER QUESTION:
{question}
"""

    response = await call_gemma(
        client,
        prompt,
        "Adversarial Skeptic"
    )

    return create_judge_critique(
        "Adversarial Skeptic",
        response
    )


# ============================================================
# FACT VERIFIER
# ============================================================

async def run_fact_verifier(
    client: genai.Client,
    question: str
) -> JudgeCritique:

    prompt = f"""
You are the FACT VERIFIER in a reasoning verification system.

Independently audit the problem.

Check:

- numerical values
- units
- arithmetic
- logical constraints
- definitions
- boundary conditions
- whether the conclusion actually follows
- whether any common assumption is incorrect

Do not agree with another answer simply because it sounds convincing.

Solve the problem yourself.

At the end:

1. State what you verified.
2. Identify any problem or inconsistency.
3. Give your proposed final answer.

USER QUESTION:
{question}
"""

    response = await call_gemma(
        client,
        prompt,
        "Fact Verifier"
    )

    return create_judge_critique(
        "Fact Verifier",
        response
    )


# ============================================================
# CHIEF ARBITER
# ============================================================

async def run_arbiter(
    client: genai.Client,
    question: str,
    critiques: list[JudgeCritique]
) -> FinalVerdict:

    judge_information = ""

    for critique in critiques:

        judge_information += f"""

============================================================
ROLE: {critique.role}
CONFIDENCE: {critique.confidence_score}%

REASONING:
{critique.assessment}

ISSUES IDENTIFIED:
{critique.identified_issues}

============================================================
"""

    prompt = f"""
You are the CHIEF ARBITER of a reasoning verification system.

Your task is to determine the most reliable answer to the original
problem using the independent analyses below.

ORIGINAL QUESTION:
{question}

INDEPENDENT JUDGES:
{judge_information}

IMPORTANT RULES:

1. Do NOT simply choose the majority answer.
2. Examine the actual reasoning.
3. A minority answer can be correct.
4. Look specifically for traps and boundary conditions.
5. Check calculations yourself.
6. Resolve contradictions explicitly.
7. Produce ONE definitive answer.

Your response MUST use exactly these three sections:

FINAL ANSWER:
Give the correct answer clearly.

RESOLVED DISCREPANCIES:
Explain which reasoning was correct and why.

KEY TRAP AVOIDED:
Explain the important mistake or trap that was avoided.
"""

    response = await call_gemma(
        client,
        prompt,
        "Chief Arbiter"
    )

    # --------------------------------------------------------
    # Extract the three sections
    # --------------------------------------------------------

    final_answer = response
    resolved = "The arbiter reviewed all available judge analyses."
    trap = "No specific trap was extracted."

    upper = response.upper()

    if "FINAL ANSWER:" in upper:

        start = upper.index("FINAL ANSWER:")
        start += len("FINAL ANSWER:")

        end = upper.find(
            "RESOLVED DISCREPANCIES:",
            start
        )

        if end == -1:
            end = len(response)

        final_answer = response[
            start:end
        ].strip()

    if "RESOLVED DISCREPANCIES:" in upper:

        start = upper.index(
            "RESOLVED DISCREPANCIES:"
        )

        start += len(
            "RESOLVED DISCREPANCIES:"
        )

        end = upper.find(
            "KEY TRAP AVOIDED:",
            start
        )

        if end == -1:
            end = len(response)

        resolved = response[
            start:end
        ].strip()

    if "KEY TRAP AVOIDED:" in upper:

        start = upper.index(
            "KEY TRAP AVOIDED:"
        )

        start += len(
            "KEY TRAP AVOIDED:"
        )

        trap = response[
            start:
        ].strip()

    return FinalVerdict(

        final_answer=final_answer,

        resolved_discrepancies=resolved,

        key_trap_avoided=trap
    )


# ============================================================
# MAIN MANY TINY JUDGES PIPELINE
# ============================================================

async def evaluate_with_judges(
    client: genai.Client,
    question: str
) -> FinalVerdict:

    print()
    print("=" * 70)
    print("MANY TINY JUDGES")
    print("=" * 70)

    print()
    print("Question:")
    print(question)

    # ========================================================
    # PHASE 1
    # ========================================================

    print()
    print("PHASE 1: INDEPENDENT REASONING")
    print("-" * 70)

    critiques = []

    # --------------------------------------------------------
    # Domain Expert
    # --------------------------------------------------------

    try:

        expert = await run_domain_expert(
            client,
            question
        )

        critiques.append(expert)

    except Exception as error:

        print(
            f"    ✗ Domain Expert unavailable: "
            f"{str(error)[:150]}"
        )

    # --------------------------------------------------------
    # Adversarial Skeptic
    # --------------------------------------------------------

    try:

        skeptic = await run_adversarial_skeptic(
            client,
            question
        )

        critiques.append(skeptic)

    except Exception as error:

        print(
            f"    ✗ Adversarial Skeptic unavailable: "
            f"{str(error)[:150]}"
        )

    # --------------------------------------------------------
    # Fact Verifier
    # --------------------------------------------------------

    try:

        verifier = await run_fact_verifier(
            client,
            question
        )

        critiques.append(verifier)

    except Exception as error:

        print(
            f"    ✗ Fact Verifier unavailable: "
            f"{str(error)[:150]}"
        )

    # ========================================================
    # CHECK JUDGES
    # ========================================================

    print()
    print(
        f"Completed judges: "
        f"{len(critiques)}/3"
    )

    if len(critiques) == 0:

        raise RuntimeError(
            "All judges failed. "
            "No reliable reasoning is available."
        )

    # ========================================================
    # SHOW JUDGES
    # ========================================================

    print()
    print("JUDGE ANALYSES")
    print("-" * 70)

    for critique in critiques:

        print()
        print(
            f"[{critique.role}]"
        )

        print(
            f"Confidence: "
            f"{critique.confidence_score}%"
        )

        print(
            critique.assessment
        )

    # ========================================================
    # PHASE 2
    # ========================================================

    print()
    print("PHASE 2: CHIEF ARBITER")
    print("-" * 70)

    verdict = await run_arbiter(
        client,
        question,
        critiques
    )

    # ========================================================
    # FINAL
    # ========================================================

    print()
    print("=" * 70)
    print("FINAL VERDICT")
    print("=" * 70)

    print()
    print("Answer:")
    print(verdict.final_answer)

    print()
    print("Resolved Discrepancies:")
    print(verdict.resolved_discrepancies)

    print()
    print("Key Trap Avoided:")
    print(verdict.key_trap_avoided)

    return verdict
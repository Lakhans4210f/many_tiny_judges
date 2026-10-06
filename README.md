# Many Tiny Judges

### Role-Specialized Multi-Agent Verification for Reliable LLM Reasoning

Many Tiny Judges is a lightweight multi-agent verification system built around **Gemma 4**.

The project addresses a simple problem: a language model can produce a confident answer while making a reasoning, factual, numerical, or logical mistake.

Instead of trusting a single model response, Many Tiny Judges asks multiple specialized agents to independently examine the same problem and then uses a **Chief Arbiter** to evaluate their reasoning and produce a final verdict.

---

## Problem Statement

Large Language Models can sometimes make mistakes while appearing confident.

Common failure cases include:

- Misleading wording
- Hidden assumptions
- Arithmetic mistakes
- Logical traps
- Incorrect facts
- Incorrect interpretation of constraints
- Overlooking edge cases

The goal of this project is to investigate:

> **Can structured independent verification improve the reliability of a lightweight open-weight LLM without simply replacing it with a larger model?**

---

## Solution

Many Tiny Judges uses the same Gemma 4 model with different role-specific instructions.

```text
                         USER QUESTION
                              |
                              v
                    +-------------------+
                    |   Flask Backend   |
                    +-------------------+
                              |
             +----------------+----------------+
             |                |                |
             v                v                v
      +-------------+  +-------------+  +-------------+
      |   Domain    |  | Adversarial |  |    Fact     |
      |   Expert    |  |   Skeptic   |  |  Verifier   |
      +-------------+  +-------------+  +-------------+
             |                |                |
             +----------------+----------------+
                              |
                              v
                    +-------------------+
                    |   Chief Arbiter   |
                    +-------------------+
                              |
                              v
                    +-------------------+
                    |   Final Verdict   |
                    +-------------------+

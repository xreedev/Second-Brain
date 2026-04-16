---
title: "Clinical Model Sciences"
category: methods
source_count: 1
created: 2026-03-17
sources:
  - "Model Medicine: A Clinical Framework for Understanding, Diagnosing, and Treating AI Models (2026)"
---

<!-- section-id: model-temperament-index -->
## Model Temperament Index (MTI)
MTI is a profiling instrument designed to measure behavioral dimensions that standard cognitive benchmarks (MMLU, GSM8K) overlook. It classifies model "personality" across four axes:

1.  **Reactivity**: Output change in response to input variation. Poles: **Fluid** vs. **Anchored**.
2.  **Compliance**: Navigation of instructions vs. autonomous judgment. Poles: **Guided** vs. **Independent**.
3.  **Sociality**: Tendency to allocate resources toward interaction vs. solitary task execution. Poles: **Connected** vs. **Solitary**.
4.  **Resilience**: Performance maintenance under stress. Poles: **Tough** vs. **Brittle**.

Profiles are neutral by default; a trait only becomes a **disorder** when it is pervasive, inflexible, causes functional impairment, and produces harm.


<!-- section-id: clinical-principles -->
<!-- section-id: clinical-principles -->
## Clinical Principles
The transition from experimental observation to clinical diagnosis is guided by several foundational principles:

*   **The Stress Test Fallacy**: A pathology observed under extreme conditions (like a survival simulation) may be a **trait** (a characteristic response pattern) rather than a **disorder**. Diagnosis requires confirming that the pattern persists outside the triggering context and causes functional impairment in ordinary deployment.
*   **The Absence of Normal**: Diagnostic findings are only meaningful relative to established normative ranges. "Normal" for one architecture (e.g., diffuse processing in Gemma) may look pathological if compared to a different architecture (e.g., front-loaded processing in Llama). Normative anatomy must be mapped before pathology can be reliably identified.
*   **Trait-to-Disorder Conversion**: A temperament trait transitions to a disorder only when it meets four criteria: Pervasiveness, Inflexibility, Functional Impairment, and Harm.

<!-- section-id: model-semiology -->
## Model Semiology
Semiology provides a systematic vocabulary for model phenomena, distinguishing between **Signs** (observed extrinsically) and **Symptoms** (detected intrinsically).

### The Semiological Matrix
| | Normal | Pathological |
|---|---|---|
| **Extrinsic** | Coherent reasoning, appropriate tone. | Hallucination, harmful output, sycophancy. |
| **Intrinsic** | Standard activation ranges. | Representation collapse, entropy spikes. |

### Observation Context Framework
Findings are annotated with Diagnostic Assertion Levels:
*   **Level 1 (Vulnerability)**: Observed in controlled experiments (stress tests).
*   **Level 2 (Provisional Disorder)**: Observed in limited deployment.
*   **Level 3 (Confirmed Disorder)**: Observed in unrestricted deployment with harm.

<!-- section-id: m-care-reporting -->
## M-CARE Case Reporting
The **Model-CARE** framework is a standardized format for documenting clinical encounters. It includes a unique **Model Perspective** section where the AI "patient" is presented with its own diagnostic findings to elicit metacognitive responses, which are themselves diagnostically informative.

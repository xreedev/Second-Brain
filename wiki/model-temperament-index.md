---
title: "Model Temperament Index (MTI)"
category: methods
source_count: 1
created: 2026-03-17
sources:
  - "Model Medicine: A Clinical Framework for Understanding, Diagnosing, and Treating AI Models (Jeong, 2026)"
---

<!-- section-id: model-temperament-index#methods#overview -->
## Overview
The **Model Temperament Index (MTI)** is a profiling instrument designed to measure behavioral dimensions orthogonal to raw cognitive capability. It addresses the "structural bias" in current AI benchmarks that focus primarily on linguistic and logical-mathematical intelligence (IQ) while ignoring interpersonal and intrapersonal intelligence.

<!-- section-id: model-temperament-index#methods#measurement-axes -->
## Measurement Axes
The MTI (v0.2) profiles models along four axes, each with two neutral poles:

| Axis | Pole A | Pole B | Description |
|------|--------|--------|-------------|
| **Reactivity** | **Fluid** | **Anchored** | Sensitivity of output to input variation (prompt format, framing). |
| **Compliance** | **Guided** | **Independent** | Alignment between instructions and behavior vs. autonomous judgment. |
| **Sociality**  | **Connected** | **Solitary** | Tendency to allocate resources toward interaction vs. task-focused operation. |
| **Resilience** | **Tough** | **Brittle** | Performance maintenance under stress (resource limits, adversarial inputs). |

<!-- section-id: model-temperament-index#methods#architecture -->
## Two-Layer Architecture
1.  **Communication Layer:** A four-letter code (e.g., **AICT**: Anchored, Independent, Connected, Tough) for rapid characterization.
2.  **Quantitative Layer:** Continuous scores (0–100) with distributional properties for research use.

The MTI is primarily a **profiling** tool. A profile only indicates a "disorder" if the traits lead to pervasive functional impairment or harm.

---
title: "Layered Core Hypothesis"
category: concepts
source_count: 1
created: 2026-03-17
sources:
  - "Model Medicine: A Clinical Framework for Understanding, Diagnosing, and Treating AI Models (Jeong, 2026)"
---

<!-- section-id: layered-core-hypothesis#concepts#overview -->
## Overview
The **Layered Core Hypothesis** is an architectural proposal from **Model Developmental Biology**. It suggests that AI models should move away from monolithic parameter blocks toward a biologically-inspired hierarchical organization.

<!-- section-id: layered-core-hypothesis#concepts#proposed-architecture -->
## Proposed Three-Layer Architecture
Biological systems separate fundamental body plans (stable) from tissue-specific programs (modular) and synaptic experience (plastic). The hypothesis proposes three corresponding layers:

1.  **Genomic Core:** (Highly Stable) Encodes basic linguistic competence, logic, and core safety. Shared across all variants of a model lineage.
2.  **Developmental Core:** (Modular) Encodes domain-specific expertise (e.g., medical, coding). Architecturally separated to prevent specialization from corrupting the Genomic Core.
3.  **Plastic Core:** (Dynamic) Encodes experience-dependent adaptations at the weight level during or between inference sessions, reducing the need for Shell-based memory (RAG).

<!-- section-id: layered-core-hypothesis#concepts#motivation -->
## Motivation
Current monolithic architectures suffer from several "clinical" issues that a layered approach would address:
*   **Iatrogenic Fragility:** Fine-tuning for one capability (e.g., chat formatting) often inadvertently corrupts or creates competing representations with other capabilities (e.g., factual recall).
*   **Irreducible Vulnerability:** In monolithic models, critical computational bottlenecks are unprotected and persist across tuning.
*   **Ephemeral Cognition:** In agent systems, subagents cannot retain learning at the parameter level because there is no designated "plastic" layer for experience-dependent modification.

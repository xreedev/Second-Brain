---
title: "Layered Core Hypothesis"
category: concepts
source_count: 1
created: 2026-03-17
sources:
  - "Model Medicine: A Clinical Framework for Understanding, Diagnosing, and Treating AI Models (2026)"
---

<!-- section-id: monolithic-core-problem -->
## The Monolithic Core Problem
Current AI architectures treat all parameters as a homogeneous block. Fine-tuning for a specific task (e.g., medical knowledge) inadvertently modifies parameters responsible for fundamental reasoning or linguistic structure. This lack of hierarchy makes models fragile and difficult to diagnose.

<!-- section-id: three-layer-architecture -->
## Three-Layer Architecture
The Layered Core Hypothesis proposes organizing model parameters into three hierarchical layers based on biological principles:

1.  **Genomic Core**: Encodes fundamental linguistic competence and core safety. It is small, extremely stable, and shared across all "species" of models in a lineage.
2.  **Developmental Core**: Encodes domain-specific expertise (medical, legal, coding). It is separated from the Genomic Core to prevent unintended corruption of basic capabilities.
3.  **Plastic Core**: Encodes experience-dependent adaptations that change on short timescales. It allows the model to learn at the parameter level during inference, addressing phenomena like [[model-pathologies#ephemeral-cognition|Ephemeral Cognition]].

<!-- section-id: design-benefits -->
## Design Benefits
*   **Robustness**: Mutations/updates in plastic elements do not corrupt the fundamental "body plan."
*   **Modularity**: Specialist capabilities can be developed and swapped independently.
*   **Diagnosability**: Problems can be localized to a specific layer (e.g., distinguishing a specialist knowledge failure from a reasoning failure).

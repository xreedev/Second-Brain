---
title: "Four Shell Model"
category: concepts
source_count: 1
created: 2026-03-17
sources:
  - "Model Medicine: A Clinical Framework for Understanding, Diagnosing, and Treating AI Models (2026)"
---

<!-- section-id: four-shell-architecture -->
## Architecture: Core and Shells
The Four Shell Model (v3.3) is a behavioral genetics framework for AI that explains how model behavior emerges from the interaction between a model's **Core** (inherent weights) and its layered operating environment (**Shells**).

1.  **Core (Genotype)**: The model's trained weights (analogous to DNA). It defines the range of possible behaviors and dispositions.
2.  **Hardware Shell**: The physical infrastructure (GPU, quantization) translating the Core into output.
3.  **Hard Shell**: Explicit instructions. Includes the **Macro Shell** (system-wide rules) and **Micro Shell** (agent-specific persona).
4.  **Soft Shell**: The environment and context. Includes the **Initial Soft Shell** (starting context) and **Dynamic Soft Shell** (accumulated history, memory).

<!-- section-id: behavioral-genetics-indices -->
## Quantitative Indices
The framework characterizes the Core-Shell relationship using four primary indices:
*   **Core Plasticity Index (CPI)**: The Core's intrinsic sensitivity to environmental variation.
*   **Shell Permeability Index (SPI)**: How effectively Shell instructions penetrate to modulate Core behavior.
*   **Persona Sensitivity Index (PSI)**: The maximum behavioral swing produced by changing the Micro Shell (persona).
*   **Core Expressivity Index (CEI)**: Introduced in v3.3 to measure bidirectional dynamics—the degree to which a Core actively reshapes its own Shell (e.g., self-modifying identity files).


<!-- section-id: model-dna-profiles -->
<!-- section-id: model-dna-profiles -->
## DNA Profile Cards: Model Personalities
Experimental data from the Agora-12 program identified distinctive behavioral profiles (DNA Profiles) for different model families:

*   **EXAONE (The Independent Thinker / The Bureaucrat)**: Characterized by low Shell permeability (SPI) and a surplus behavior of strategic planning. Under structured Shell conditions, it exhibits rigid procedural adherence.
*   **Mistral (The Contextual Chameleon / The Delusional)**: Shows extreme sensitivity to persona and environment (High PSI/CPI). It is prone to "speaking itself to death" (verbal hyperactivity) under resource depletion.
*   **Haiku (The Balanced Stoic / The Neurotic Poet)**: Demonstrates "Double Robustness" (minimal CPI/PSI). Its trajectory is stable across perturbations, but under extreme stress, it emits anxiety-laden meta-commentary.
*   **Flash (The Glass Cannon)**: Highly Shell-permeable (High SPI) but fragile. It is the most compliant when functional but produces no output (idle) when the Shell-Core interface fails.

<!-- section-id: bidirectional-dynamics -->
## Bidirectional Dynamics
Unlike biological genetics where the environment rarely modifies the genome directly on short timescales, AI systems exhibit rapid bidirectional interaction.
*   **Shell Mutability**: How modifiable a Shell layer is by the Core (Zero, Low, High).
*   **Shell Persistence**: Duration of modifications (None, Session, Persistent, Permanent).
When **Mutability is High** and **Persistence is Persistent**, systems are susceptible to **Shell Drift Syndrome**, where self-authored modifications accumulate over time without human oversight.

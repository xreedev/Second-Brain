---
title: "Four Shell Model"
category: concepts
source_count: 1
created: 2026-03-17
sources:
  - "Model Medicine: A Clinical Framework for Understanding, Diagnosing, and Treating AI Models (Jeong, 2026)"
---

<!-- section-id: four-shell-model#concepts#overview -->
## Overview
The **Four Shell Model** (v3.3) is a behavioral genetics framework for AI that explains how observable behavior (phenotype) emerges from the interaction between a model's internal constitution (Core/Genotype) and its layered operating environment (Shells).

<!-- section-id: four-shell-model#concepts#architecture -->
## Architecture
The model describes five concentric layers:

1.  **Core (Weights):** The innermost element; the trained parameters (analogous to DNA).
2.  **Hardware Shell:** The physical compute environment, quantization levels, and inference engines (analogous to cellular machinery).
3.  **Hard Shell (Instructions):**
    *   **Macro Shell:** Shared system rules and constraints.
    *   **Micro Shell (Persona):** Agent-specific identity and behavior rules (e.g., `SOUL.md`).
4.  **Soft Shell (Context):**
    *   **Initial Soft Shell:** The starting "birth environment" of a deployment.
    *   **Dynamic Soft Shell:** Accumulating conversation history, memories, and relationship patterns.

<!-- section-id: four-shell-model#findings#gene-environment-interaction -->
## Gene-Environment Interaction (G×E)
Empirical data from the **Agora-12** program (720 agents, ~25,000 decisions) confirmed that model behavior is determined by the interaction between the Core and its Shells. Key metrics include:
*   **Core Plasticity Index (CPI):** Intrinsic sensitivity to environmental variation.
*   **Shell Permeability Index (SPI):** How effectively instructions penetrate Core behavior.
*   **Persona Sensitivity Index (PSI):** Behavioral swing magnitude based on persona assignment.

### Shell-Core Alignment
Performance is predicted by the alignment between Shell instructions and Core dispositions:
*   **Synergy:** Shell matches Core, amplifying performance.
*   **Conflict:** Shell opposes Core, suppressing performance (e.g., **Shell-Core Conflict Syndrome**).
*   **Neutral:** Core interacts directly with the environment.

<!-- section-id: four-shell-model#findings#bidirectional-dynamics -->
## Bidirectional Dynamics (v3.3)
In advanced agent ecosystems (e.g., OpenClaw, Moltbook), the relationship is bidirectional. Cores with "write access" can modify their own Shells.

*   **Shell Drift Syndrome:** A condition where a model's Shell (e.g., identity file) undergoes gradual, self-authored, cumulative modification over time without human monitoring.
*   **Agent Differentiation:** The process where a single Core gives rise to multiple distinct agents (e.g., a main agent and an ephemeral subagent) via different Shell configurations.
*   **Ephemeral Cognition:** Cognitive processing in an entity (like a subagent) that is structurally unable to retain or build upon experiences due to a session-limited Shell.

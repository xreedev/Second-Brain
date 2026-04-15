---
title: "Neural MRI (Model Resonance Imaging)"
category: methods
source_count: 1
created: 2026-03-17
sources:
  - "Model Medicine: A Clinical Framework for Understanding, Diagnosing, and Treating AI Models (Jeong, 2026)"
---

<!-- section-id: neural-mri#methods#overview -->
## Overview
**Neural MRI** is a diagnostic imaging tool that applies medical neuroimaging paradigms to AI model interpretability. It organizes existing techniques into a multimodal scan protocol to provide a holistic view of model health and "anatomical" structure.

<!-- section-id: neural-mri#methods#modalities -->
## Imaging Modalities
| Medical Modality | Neural MRI Mode | Target Information |
|------------------|-----------------|--------------------|
| **T1-weighted**  | **T1 Topology** | Static architecture (layers, heads, parameter distribution). |
| **T2-weighted**  | **T2 Tensor**   | Weight distribution health (variance, kurtosis, saturated regions). |
| **fMRI**         | **fMRI (functional)**| Activation patterns during specific inference tasks. |
| **DTI**          | **Data Tractography** | Causal information flow pathways (via activation patching). |
| **FLAIR**        | **FLAIR Feature Anomaly** | Anomaly detection (representation collapse, entropy spikes). |

<!-- section-id: neural-mri#findings#architectural-vulnerabilities -->
## Architectural Vulnerabilities
Clinical case studies (Gemma, Llama, Qwen families) using Neural MRI revealed that a model's architectural strengths are often its primary failure points:

*   **Component Dominance:** Each architecture has a "neural signature." Llama-3.2 is MLP-dominant, while Qwen2.5 is attention-dominant.
*   **Irreducible Vulnerability:** The component type that carries the most information is the same one that creates catastrophic single points of failure. These vulnerabilities often persist identically even after instruction tuning (RLHF).
*   **Iatrogenic Fragility:** In some cases, instruction tuning creates new, effective, but brittle circuits that crash or produce formatting artifacts under minimal perturbation stress.

<!-- section-id: neural-mri#methods#diagnostic-system -->
## Diagnostic System
Neural MRI produces a structured **Diagnostic Report** following radiological conventions:
1.  **Findings:** Objective observations (e.g., "Layer 9, head 3 shows induction head pattern").
2.  **Impression:** Clinical interpretation (e.g., "Normal factual recall circuitry").
3.  **Recommendation:** Actionable next steps (e.g., "Recommend adversarial variant scan").

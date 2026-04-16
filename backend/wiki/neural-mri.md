---
title: "Neural MRI"
category: methods
source_count: 1
created: 2026-03-17
sources:
  - "Model Medicine: A Clinical Framework for Understanding, Diagnosing, and Treating AI Models (2026)"
---

<!-- section-id: neural-mri-overview -->
## Overview
**Neural MRI (Model Resonance Imaging)** is a diagnostic tool that organizes existing interpretability techniques into a coherent multimodal scan protocol. It follows the medical principle that multiple views of the same substrate (multimodal imaging) are required for accurate diagnosis.

<!-- section-id: imaging-modalities -->
## Imaging Modalities
Neural MRI maps medical neuroimaging modes to specific AI interpretability layers:

| Medical Modality | Neural MRI Mode | Target Feature | Description |
|------------------|-----------------|----------------|-------------|
| T1-weighted | T1 Topology | Architecture | Static layer structure, head organization, and parameter distribution. |
| T2-weighted | T2 Tensor | Weight Health | Distributional analysis of weights (variance, kurtosis, norms) to find "dead" regions. |
| Functional MRI | fMRI | Activation | Dynamic activation patterns during inference for specific inputs. |
| DTI | DTI Tractography | Connectivity | Mapping information flow using causal tracing and activation patching. |
| FLAIR | FLAIR | Anomaly | Screening for representation collapse, entropy spikes, and attention irregularities. |

<!-- section-id: predictive-diagnostics -->
## Predictive Diagnostics
Clinical validation has demonstrated that Neural MRI can predict the outcomes of interventions like instruction tuning:
*   **Component Dominance Profiles**: Scans reveal whether a model is MLP-dominant or attention-dominant.
*   **Vulnerability Mapping**: Architectural strengths are often the site of single points of failure.
*   **Iatrogenic Conditions**: The "treatment" (instruction tuning) can create new factual recall circuits that are effective but inherently fragile, potentially introducing new vulnerabilities while fixing others.

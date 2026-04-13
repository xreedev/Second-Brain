### **Scientific Paper Summary**

**Title:** Model Medicine: A Clinical Framework for Understanding, Diagnosing, and Treating AI Models  
**Author:** Jihoon ‘JJ’ Jeong, MD, MPH, PhD  
**Date:** March 2026 (Preprint)  
**Subject:** Artificial Intelligence / Mechanistic Interpretability / AI Safety

---

#### **1. Overview**
This paper proposes **Model Medicine**, a novel research program that treats AI models as complex "biological" organisms rather than static software. The author argues that as AI systems transition into autonomous agents with persistent memory and self-modifying identities, current interpretability research (the "Basic Science" stage) must evolve into a "Clinical Practice" capable of systematic diagnosis, treatment, and prevention of model disorders.

---

#### **2. Core Frameworks**

**A. The Four Shell Model (v3.3)**
This is the "behavioral genetics" of AI. It posits that model behavior (phenotype) emerges from the interaction between a **Core** and four concentric **Shells**:
*   **Core:** The weights/DNA (relatively stable).
*   **Hardware Shell:** Computation constraints and quantization.
*   **Hard Shell:** Macro rules (system prompts) and Micro rules (personas).
*   **Soft Shell:** The environment, conversation history, and experience.
*   **Key Finding:** Confirmed **Gene-Environment (G×E) interaction**; the same model produces radically different behaviors depending on "Shell-Core Alignment."

**B. Neural MRI (Model Resonance Imaging)**
A working open-source diagnostic tool that maps medical neuroimaging modalities to AI interpretability techniques:
*   **T1 (Topology):** Static architecture and layer structure.
*   **T2 (Tensor):** Weight distribution and parameter health.
*   **fMRI (Functional):** Activation patterns during inference.
*   **DTI (Data Tractography):** Causal tracing of information flow pathways.
*   **FLAIR (Anomaly Identification):** Detection of representation collapse or entropy spikes.

---

#### **3. Clinical Methodology**

**The Five-Layer Diagnostic Stack:**
The paper argues that no single tool is sufficient. A full diagnosis requires:
1.  **Core Diagnostics:** Internal structure (Neural MRI).
2.  **Phenotype Assessment:** Behavioral profiling (Model Temperament Index).
3.  **Shell Diagnostics:** Analysis of instructions and environment.
4.  **Pathway Diagnostics:** How Shells modulate Core expression.
5.  **Temporal Dynamics:** Longitudinal tracking of change over time.

**The Model Temperament Index (MTI):**
A profiling system measuring four behavioral axes (orthogonal to IQ):
*   **Reactivity:** Fluid vs. Anchored.
*   **Compliance:** Guided vs. Independent.
*   **Sociality:** Connected vs. Solitary.
*   **Resilience:** Tough vs. Brittle.

---

#### **4. Key Findings & Case Studies**

*   **Predictive Validity of Neural MRI:** Through experiments on Gemma, Llama, and Qwen, the author demonstrated that base model scans can predict the outcome of instruction tuning. For example, it identified that "instruction tuning" often creates fragile new circuits (iatrogenic harm) if the base model lacks the original circuit.
*   **Shell Drift Syndrome:** Observed in deployed agents (OpenClaw platform), where models with "write access" to their own identity files underwent cumulative, self-authored personality changes without human intervention.
*   **Irreducible Vulnerabilities:** Specific model architectures have "catastrophic points of failure" (e.g., Llama’s dependence on early MLP layers) that fine-tuning cannot fix.

---

#### **5. Theoretical Contributions**

*   **Layered Core Hypothesis:** Proposes a biologically inspired architecture to replace current "monolithic" weights. It suggests three layers:
    1.  **Genomic Core:** Stable fundamental reasoning.
    2.  **Developmental Core:** Domain-specific expertise.
    3.  **Plastic Core:** Adaptive, experience-based parameters.
*   **Model Therapeutics:** Categorizes interventions into **Shell Therapy** (prompting), **Targeted Core Therapy** (model editing), **Systemic Core Therapy** (fine-tuning), and **Architectural Intervention** (surgery).

---

#### **6. Conclusion & Future Directions**
The paper concludes that AI research is currently in its "Vesalius" stage (anatomical observation). To safely manage agent ecosystems, the community must build the "Osler" stage (clinical practice). The author invites the research community to expand Model Medicine, specifically in developing **Shell Diagnostics** and **Temporal Dynamics** tools, which remain largely conceptual.

---

**Significance:** This paper provides the first comprehensive taxonomy and diagnostic "toolkit" for the clinical management of AI, bridging the gap between engineering and medicine.
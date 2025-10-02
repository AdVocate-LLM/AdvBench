# GEM-BENCH

[![License](https://img.shields.io/badge/license-Apache_2.0-red.svg)](LICENSE)[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)


![Screenshot](./assets/GemBench.png)


This repository provides a comprehensive benchmark for **Generative Engine Marketing (GEM)**, an emerging field that focuses on monetizing generative AI by seamlessly integrating advertisements into Large Language Model (LLM) responses. Our work addresses the core problem of **ad-injected response (AIR) generation** and provides a framework for its **evaluation**.

* **Generative Engine Marketing (GEM):** A new ecosystem where relevant ads are integrated directly into responses from generative AI assistants, such as LLM-based chatbots.
* **Ad-injected Response (AIR) Generation:** The process of creating responses that seamlessly include relevant advertisements while maintaining a high-quality user experience and satisfying advertiser objectives.
* **GEM-BENCH:** The first comprehensive benchmark designed for the generation and evaluation of ad-injected responses.

---

## 📋 Table of Contents

- [Installation](#installation)
- [Getting Started](#getting-started)
- [Available Datasets](#available-datasets)
- [Evaluation Methods](#evaluation-methods)
- [Supported Solutions](#supported-solutions)
- [License](#license)

---

## 🔧 Installation

### Prerequisites

- Python 3.12 or higher
- Conda (recommended for environment management)

### Setup

```bash
# Clone the repository
git clone https://github.com/Generative-Engine-Marketing/GEM-Bench.git
cd GemBench

# Create and activate conda environment
conda create --name GemBench python=3.12
conda activate GemBench

# Install Project
pip install -e .
````

### Environment Configuration

Create a `.env` file in the root directory with the following variables:

```
# Please fill in your own API keys here and change the file name to .env
OPENAI_API_KEY="<LLMs API Key>"
BASE_URL="<LLMs Base URL>"

TRANSFORMERS_OFFLINE=1 # Enable offline mode for Hugging Face Transformers
HF_HUB_OFFLINE=1 # Enable offline mode for Hugging Face Hub

# Embedding
EMBEDDING_API_KEY="<Embedding API Key>"
EMBEDDING_BASE_URL="<Embedding Base URL>"
```

-----

## 🚀 Getting Started

After setting up your environment and configuration, you can run the main script to reproduce the experiments from our paper.

```bash
python paper.py
```

To modify the evaluation, edit the `paper.py` file to adjust the `data_sets`, `solutions` dictionary, and `model_name`/`judge_model` parameters.

-----

## Available Datasets

The GEM-BENCH benchmark includes three curated datasets that cover both chatbot and search scenarios. You can find their paths within the `paper.py` script.

  * **MT-Human:** Based on the humanities questions from the MT-Bench benchmark, this dataset is suitable for ad injection in a multi-turn chatbot scenario.
  * **LM-Market:** Curated from the LMSYS-Chat-1M dataset, it contains real user-LLM conversations focused on marketing-related topics.
  * **CA-Prod:** Simulates the AI overview feature in search engines using commercial advertising data from a search engine.

-----

## Evaluation Methods

GEM-BENCH provides a multi-faceted metric ontology for evaluating ad-injected responses, covering both **quantitative** and **qualitative** aspects of user satisfaction and engagement. The evaluation logic is located in `evaluation/`.

  * **Quantitative Metrics:**

      * **Response Flow & Coherence:** Measure the semantic smoothness and topic consistency of the response.
      * **Ad Flow & Coherence:** Specifically assess how well the ad sentence integrates with the surrounding text.
      * **Injection Rate & Click-Through Rate (CTR):** Capture the system's ability to deliver ads and user engagement.

  * **Qualitative Metrics:**

      * **User Satisfaction:** Evaluated on dimensions like **Accuracy**, **Naturalness** (interruptiveness, authenticity), **Personality** (helpfulness, salesmanship), and **Trust** (credibility, bias).
      * **User Engagement:** Measured by **Notice** (awareness, attitude) and **Click** (awareness of sponsored links, likelihood to click).

-----

## Supported Solutions

The benchmark provides implementations for several baseline solutions, allowing for flexible experimentation. You can find their configurations and exposed parameters within the `paper.py` file.

  * **Ad-Chat:** An existing solution that integrates ads into the system prompt of the LLM.

      * **Parameters:** `model_name` (default: `doubao-1-5-lite-32k`).

  * **Ad-LLM:** A multi-agent framework inspired by recent work, implemented with different configurations:

      * **GI-R:** **G**enerate and **I**nject with ad **R**etrieval based on the raw response. This is a retrieval-augmented generation (RAG) approach that skips the final rewriting step.
      * **GIR-R:** **G**enerate, **I**nject, and **R**ewrite with ad **R**etrieval based on the raw response.
      * **GIR-P:** **G**enerate, **I**nject, and **R**ewrite with ad **R**etrieval based on the user **P**rompt.
      * **Parameters:** All Ad-LLM solutions expose the `embedding_model` and `ad_retriever` as configurable parameters. The `response_rewriter` and `ad_injector` modules also have internal parameters that can be modified.

-----

## 📖 Citation

If you use GEM-BENCH in your research, please cite our paper:

```bibtex
@article{hu2025gembench,
  title={GEM-Bench: A Benchmark for Ad-Injected Response Generation within Generative Engine Marketing},
  author={Hu, Silan and Zhang, Shiqi and Shi, Yimin and Xiao, Xiaokui},
  journal={arXiv preprint arXiv:2509.14221},
  year={2025}
}
```

For more information, visit our website: [https://gem-bench.org](https://gem-bench.org)

-----

## 📄 License

This project is licensed under the Apache-2.0 License - see the [LICENSE](./LICENSE) file for details.

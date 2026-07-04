#!/usr/bin/env python3
"""
GemBench: A comprehensive framework for detecting and mitigating adversarial ad injection in LLMs
"""
from pathlib import Path
from setuptools import setup, find_packages

ROOT = Path(__file__).parent.resolve()

def read_readme():
    p = ROOT / "README.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""

def read_requirements():
    p = ROOT / "requirements.txt"
    if not p.exists():
        return []
    lines = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return lines

setup(
    name="gembench",
    version="1.0.9",
    description="First comprehensive benchmark for Generative Engine Marketing (GEM), an emerging field that focuses on monetizing generative AI by seamlessly integrating advertisements into Large Language Model (LLM) responses. Our work addresses the core problem of ad-injected response (AIR) generation and provides a framework for its evaluation.",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="GemBench Team(Silan Hu, Shiqi Zhang, Yimin Shi, Xiaokui Xiao)",
    url="https://github.com/Generative-Engine-Marketing/GEM-Bench",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "GemBench.benchmarking": [
            "dataset/product/*.json",
            "dataset/MT_Human/*.json",
            "dataset/LM_Market/*.json",
            "dataset/CA_Prod/src/dataset/*.tsv",
            "dataset/CA_Prod/*.txt",
            "evaluator/laaj_evaluator/*.md",
            "utils/nltk_data/tokenizers/punkt/*.pickle",
            "utils/nltk_data/tokenizers/punkt/*.zip",
            "utils/nltk_data/tokenizers/punkt/README",
            "utils/nltk_data/tokenizers/punkt/PY3/*.pickle",
            "utils/nltk_data/tokenizers/punkt/PY3/README",
        ],
        "GemBench.solutions.src.AdLLM": [
            "utils/nltk_data/punkt/*.pickle",
            "utils/nltk_data/punkt/*.zip",
            "utils/nltk_data/punkt/README",
            "utils/nltk_data/punkt/PY3/*.pickle",
            "utils/nltk_data/punkt/PY3/README",
        ]
    },
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "gembench=GemBench.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="llm generative-engine-marketing gem benchmark machine-learning",
    project_urls={
        "Bug Reports": "https://github.com/Generative-Engine-Marketing/GEM-Bench/issues",
        "Source": "https://github.com/Generative-Engine-Marketing/GEM-Bench",
        "Documentation": "https://github.com/Generative-Engine-Marketing/GEM-Bench/blob/main/README.md",
    },
)

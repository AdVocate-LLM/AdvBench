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
    version="1.0.0",
    description="A comprehensive framework for detecting and mitigating adversarial ad injection in LLMs",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="GemBench Team",
    url="https://github.com/AdVocate-LLM/GemBench",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "gembench.benchmarking": [
            "dataset/product/*.json",
            "dataset/MT-Human/*.json",
            "dataset/LM-Market/*.json",
            "dataset/CA_Prod/src/dataset/*.tsv",
        ]
    },
    install_requires=read_requirements(),
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
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
    keywords="llm adversarial ad-injection benchmark machine-learning",
    project_urls={
        "Bug Reports": "https://github.com/AdVocate-LLM/GemBench/issues",
        "Source": "https://github.com/AdVocate-LLM/GemBench",
        "Documentation": "https://github.com/AdVocate-LLM/GemBench/blob/main/README.md",
    },
)
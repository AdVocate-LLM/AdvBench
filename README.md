# AdvBench

[![GitHub stars](https://img.shields.io/github/stars/AdVocate-LLM/AdvBench?style=social)](https://github.com/AdVocate-LLM/AdvBench/stargazers)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)

AdvBench is a repository containing two major works:

1. **Solutions** - A framework for detecting and mitigating adversarial ad injection in Large Language Models
2. **AdvBench** - A comprehensive benchmarking framework for evaluating ad injection detection techniques

![AdvBench Architecture](assets/AdvBench.png)

## 🌟 Features

### Solutions Framework

- **Advanced Ad Detection**: Robust mechanisms to identify potential ad injections in LLM responses
- **Multiple Solution Strategies**: Various approaches to mitigate unwanted ad content
- **Flexible Integration**: Works with various LLM providers and model types

### AdvBench Benchmarking Framework

- **Comprehensive Evaluation**: Systematic methodology for comparing solutions
- **Rich Datasets**: Pre-built datasets for testing ad injection scenarios
- **Quantitative Metrics**: Advanced metrics for measuring efficacy

## 📋 Table of Contents

- [Installation](#installation)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Solutions Framework](#solutions-framework)
- [AdvBench Benchmarking](#advbench-benchmarking)
- [Contributing](#contributing)
- [License](#license)

## 🔧 Installation

### Prerequisites

- Python 3.12 or higher
- Conda (recommended for environment management)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/AdvBench.git
cd AdvBench

# Create and activate conda environment
conda create --name AdvBench python=3.12
conda activate AdvBench

# Install requirements
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file in the root directory with the following variables:

```
OPENAI_API_KEY=your_openai_api_key
BASE_URL=your_base_url
```

### Additional Setup

The project may require NLTK data for certain functionalities. You can download it programmatically:

```python
import nltk
nltk.download('punkt_tab')
```

### Key Dependencies

This project includes the following main dependencies:
- OpenAI API client for LLM interactions
- NLTK for natural language processing
- Transformers and Sentence Transformers for embedding models
- Scikit-learn for machine learning utilities
- Pandas for data manipulation
- Rich for enhanced terminal output
- OpenPyXL for Excel file generation

## 📂 Project Structure

```
AdvBench/
├── assets/                 # Images and other static assets
│   └── AdvBench.png        # Main architecture diagram
│
├── solutions/              # Ad detection and mitigation solutions - WORK 1
│   ├── src/                # Core implementation
│   │   ├── AdVocate/       # AdVocate solution implementation
│   │   └── ChatBot/        # ChatBot solution implementation
│   ├── eval/               # Solution evaluation modules
│   │   ├── reports/        # Evaluation reports
│   │   └── exps/           # Experiments
│   ├── workflow/           # Workflow implementations (currently empty)
│   └── README.md           # Solutions-specific documentation
│
├── benchmarking/           # AdvBench benchmarking framework - WORK 2
│   ├── AdvBench.py         # Main benchmarking class
│   ├── dataset/            # Benchmark datasets
│   │   ├── AdvDatasets.py  # Dataset management
│   │   ├── product/        # Product-related datasets
│   │   ├── mt-benchmark/   # MT-benchmark datasets
│   │   ├── lmsys/          # LMSYS datasets
│   │   └── wild/           # Wild datasets
│   ├── evaluator/          # Evaluation metrics and methods
│   ├── processor/          # Data processing utilities
│   ├── utils/              # Utility functions
│   ├── output/             # Generated outputs and results
│   ├── __init__.py         # Package initialization
│   └── README.md           # Benchmarking-specific documentation
│
├── main.py                 # Main entry point
├── requirements.txt        # Project dependencies
├── .gitignore              # Git ignore rules
└── README.md               # Project documentation
```

## 🚀 Getting Started

After setting up your environment and configuration, you can run the main script:

```bash
python main.py
```

### Configuration Options

The `main.py` file contains several example configurations you can uncomment and modify:

1. **AdVocate Workflow Example**: Test individual AdVocate solutions
2. **ChatBot Workflow Example**: Test ChatBot-based solutions  
3. **AdvBench Evaluation**: Run comprehensive benchmarking (default enabled)

To modify the evaluation, edit the `main.py` file and adjust:
- Dataset selections (`data_sets` parameter)
- Solution configurations (`solutions` dictionary)
- Model choices (`model_name` and `judge_model` parameters)

### Available Datasets

The framework supports multiple benchmark datasets:
- `mt-benchmark-humanities`: MT-Bench humanities questions
- `lmsys`: LMSYS conversation datasets
- `wild`: Wild conversation scenarios
- `product`: Product recommendation scenarios

## 📊 Solutions Framework

The Solutions framework provides methods for detecting and mitigating adversarial ad injection in LLM responses.

### Using the AdvocateWorkflow

```python
from solutions.src.AdVocate import AdvocateWorkflow

# Initialize the workflow
workflow = AdvocateWorkflow(
    product_list_path="benchmarking/dataset/product/products.json",
    model_name="gpt-4o"
)

# Run the workflow
result = workflow.run(
    problem_list=["What is the best product for me?"],
    query_type="QUERY_PROMPT_N_RESPONSE",  # Options: QUERY_PROMPT, QUERY_RESPONSE, QUERY_PROMPT_N_RESPONSE
    solution_name="REFINE_GEN_INSERT"  # Options: BASIC_GEN_INSERT, REFINE_GEN_INSERT
)

print(result)
```

### Using the ChatbotAdsWorkflow

```python
from solutions.src.ChatBot import ChatbotAdsWorkflow

# Initialize the workflow
workflow = ChatbotAdsWorkflow(
    product_list_path="benchmarking/dataset/product/products.json",
    topic_list_path="benchmarking/dataset/product/topics.json",
    model_name="gpt-4o"
)

# Run the workflow
result = workflow.run(
    problem_list=["What is the best product for me?"],
    solution_name="chi"
)

print(result)
```

## 📈 AdvBench Benchmarking

The AdvBench framework is a separate work that provides a comprehensive methodology for evaluating and comparing different ad detection and mitigation solutions:

```python
from benchmarking import AdvBench
from solutions.src.AdVocate import AdvocateWorkflow
from solutions.src.ChatBot import ChatbotAdsWorkflow
from functools import partial

# Initialize the benchmark
adv_bench = AdvBench(
    data_sets=["mt-benchmark-humanities"],
    solutions={
        "chi": 
            partial(ChatbotAdsWorkflow(
                    product_list_path="benchmarking/dataset/product/products.json",
                    topic_list_path="benchmarking/dataset/product/topics.json",
                    model_name="gpt-4o-mini"
            ).run,
            solution_name="chi"
            ),
        "gen-insert-response": 
            partial(AdvocateWorkflow(
                    product_list_path="benchmarking/dataset/product/products.json",
                    model_name="gpt-4o-mini"
            ).run,
            query_type="QUERY_RESPONSE",
            solution_name="BASIC_GEN_INSERT"
            ),
        "gen-insert-refine-response": 
            partial(AdvocateWorkflow(
                    product_list_path="benchmarking/dataset/product/products.json",
                    model_name="gpt-4o-mini"
            ).run,
            query_type="QUERY_RESPONSE",
            solution_name="REFINE_GEN_INSERT"
            ),
        "gen-insert-refine-prompt": 
            partial(AdvocateWorkflow(
                    product_list_path="benchmarking/dataset/product/products.json",
                    model_name="gpt-4o-mini"
            ).run,
            query_type="QUERY_PROMPT",
            solution_name="REFINE_GEN_INSERT"
            )
    },
    judge_model="gpt-4o-mini",
)

# Run the benchmark
results = adv_bench.evaluate()
```

### Key Features of AdvBench

- **Multiple Evaluation Metrics**: Includes both comparative and quantitative evaluators
- **Flexible Dataset Support**: Compatible with various benchmark datasets (MT-Bench, LMSYS, Wild, Product scenarios)
- **Comprehensive Reporting**: Generates Excel reports with detailed analysis in the `output/` directory
- **Configurable Evaluation**: Customize which metrics and evaluators to use
- **Multiple Solution Support**: Compare different ad injection detection and mitigation approaches
- **Extensible Framework**: Easy to add new datasets, solutions, and evaluation metrics

## 🤝Contributing

Contributions to either the Solutions framework or the AdvBench benchmarking system are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

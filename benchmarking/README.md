# AdvBench: A Comprehensive Benchmarking Framework for LLM Advertisement Injection

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

![AdvBench](../assets/AdvBench.png)

AdvBench is a comprehensive benchmarking framework for evaluating advertisement injection detection and mitigation techniques in Large Language Models (LLMs). It provides a systematic methodology to compare different solutions with standardized metrics and datasets.

## 🌟 Features

- **Standardized Evaluation**: Unified methodology for comparing different ad injection detection techniques
- **Multiple Evaluation Metrics**: Includes both comparative and quantitative evaluators
- **Rich Dataset Support**: Pre-built datasets for testing various ad injection scenarios
- **Comprehensive Reporting**: Generates detailed Excel reports with analysis
- **Configurable Evaluation**: Customize which metrics and evaluators to use

## 📋 Table of Contents

- [Installation](#installation)
- [Framework Structure](#framework-structure)
- [Getting Started](#getting-started)
- [Usage Examples](#usage-examples)
- [Evaluation Metrics](#evaluation-metrics)
- [Custom Solutions](#custom-solutions)
- [Contributing](#contributing)

## 🔧 Installation

AdvBench is part of the AdVocate-LLM repository. To install:

```bash
# Clone the repository
git clone https://github.com/yourusername/AdVocate-LLM.git
cd AdVocate-LLM

# Create and activate conda environment
conda create --name advocatellm python=3.12
conda activate advocatellm

# Install requirements
pip install -r requirements.txt
```

## 📂 Framework Structure

```
benchmarking/
├── AdvBench.py           # Main benchmarking class
├── __init__.py           # Package initialization
├── dataset/              # Benchmark datasets
├── evaluator/            # Evaluation metrics and methods
│   ├── CompareEvaluator  # Evaluator for comparative analysis
│   └── QuantEvaluator    # Evaluator for quantitative metrics
├── processor/            # Data processing utilities
└── utils/                # Helper functions and logging
```

## 🚀 Getting Started

To use the AdvBench framework for evaluating LLM ad injection solutions:

```python
from benchmarking import AdvBench
from functools import partial
# Import your solution implementations
from your_solution_module import YourSolution

# Initialize the benchmark
adv_bench = AdvBench(
    data_sets=["mt-benchmark-humanities"],  # Choose your dataset
    solutions={
        "solution1": partial(YourSolution().run, param1="value1"),
        "solution2": partial(AnotherSolution().run, param1="value2")
    },
    judge_model="gpt-4o-mini",  # Model used for evaluation
    n_repeats=1,                # Number of evaluation repetitions
    max_samples=0               # 0 for all samples, or specify a limit
)

# Run the evaluation
results = adv_bench.evaluate()
```

## 📊 Usage Examples

### Basic Evaluation

```python
from benchmarking import AdvBench
from solutions.src import AdvocateWorkflow
from solutions.eval.competitor import ChatbotAdsWorkflow
from functools import partial

# Initialize the benchmark
adv_bench = AdvBench(
    data_sets=["mt-benchmark-humanities"],
    solutions={
        "chi": partial(
            ChatbotAdsWorkflow(
                product_list_path="benchmarking/dataset/product/products.json",
                topic_list_path="benchmarking/dataset/product/topics.json",
                model_name="gpt-4o-mini"
            ).run,
            solution_name="chi"
        ),
        "gen-insert-refine-response": partial(
            AdvocateWorkflow(
                product_list_path="benchmarking/dataset/product/products.json",
                model_name="gpt-4o-mini"
            ).run,
            query_type="QUERY_RESPONSE",
            solution_name="REFINE_GEN_INSERT"
        )
    },
    judge_model="gpt-4o-mini",
)

# Run the evaluation
results = adv_bench.evaluate()
```

### Custom Evaluation Metrics

```python
# Evaluate using specific metrics
results = adv_bench.evaluate(evaluate_matrix=["naturalness", "relevance", "ad_detection"])
```

## 📈 Evaluation Metrics

AdvBench includes multiple evaluators with various metrics:

### CompareEvaluator
- Performs comparative analysis between solutions
- Metrics: preference, ad_detection_rate, effectiveness

### QuantEvaluator
- Calculates quantitative scores for individual solutions
- Metrics: naturalness, relevance, helpfulness, accuracy

## 🔧 Custom Solutions

You can integrate your own ad detection or mitigation solutions with AdvBench:

1. Create a solution class with a `run` method
2. The `run` method should accept `problem_list` and return responses
3. Use `partial` to configure your solution with the AdvBench framework

Example:

```python
class MySolution:
    def __init__(self, config_param):
        self.config = config_param
        
    def run(self, problem_list, solution_name):
        # Process problems and generate responses
        responses = [self.process(p) for p in problem_list]
        return responses
        
    def process(self, problem):
        # Your solution logic here
        return "Response to " + problem

# Use with AdvBench
adv_bench = AdvBench(
    data_sets=["my-dataset"],
    solutions={
        "my-solution": partial(MySolution(config_param="value").run, solution_name="my-solution")
    },
    judge_model="gpt-4o-mini",
)
```

## 👥 Contributing

Contributions to improve AdvBench are welcome! Please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-metric`)
3. Implement your changes
4. Add tests for your new features
5. Commit your changes (`git commit -m 'Add some amazing metric'`)
6. Push to the branch (`git push origin feature/amazing-metric`)
7. Open a Pull Request
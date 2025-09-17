# Solutions Framework

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

This directory contains comprehensive solutions for detecting and mitigating adversarial ad injection in Large Language Models (LLMs). The Solutions framework is **Work 1** of the AdvBench project, complementing the benchmarking framework to provide a complete evaluation ecosystem.

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [AdVocate Framework](#advocate-framework)
- [ChatBot Framework](#chatbot-framework)
- [Getting Started](#getting-started)
- [Usage Examples](#usage-examples)
- [Integration with AdvBench](#integration-with-advbench)
- [Evaluation](#evaluation)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)

## 🔍 Overview

The Solutions framework provides:

- **Advanced Ad Detection**: Robust mechanisms to identify potential ad injections in LLM responses
- **Multiple Solution Strategies**: Various approaches to mitigate unwanted ad content
- **Multi-Agent Architecture**: Sophisticated agent-based approach for ad detection and injection
- **Parallel Processing**: Efficient batch processing capabilities for large-scale evaluation
- **Flexible Workflows**: Configurable pipelines for different use cases
- **RAG Integration**: Retrieval-Augmented Generation for product-aware responses
- **Comprehensive Evaluation**: Built-in evaluation modules for performance assessment
- **Flexible Integration**: Works with various LLM providers and model types

## 📂 Project Structure

```
solutions/
├── src/                    # Core solution implementations
│   ├── AdVocate/          # Multi-agent ad injection framework
│   │   ├── agents/        # Agent implementations
│   │   │   ├── answer_agent.py      # Raw answer generation agent
│   │   │   ├── injector_agent.py    # Ad injection agent
│   │   │   └── base_agent.py        # Base agent class
│   │   ├── config/        # Configuration files
│   │   ├── prompt/        # Prompt templates
│   │   ├── tools/         # Utility tools
│   │   ├── utils/         # Helper utilities
│   │   └── workflow.py    # Main workflow orchestrator
│   │
│   └── ChatBot/           # Chatbot-based ad injection framework
│       ├── src/           # ChatBot core implementation
│       ├── chatbotAdsWorkflow.py  # Main workflow
│       └── __init__.py
│
├── eval/                  # Evaluation modules
│   ├── reports/          # Generated evaluation reports
│   └── exps/             # Experimental configurations
│
└── workflow/             # Additional workflow utilities
```

## 🔧 Installation & Setup

### Prerequisites

- Python 3.12 or higher
- Conda (recommended for environment management)

### Environment Setup

From the project root directory:

```bash
# Create and activate conda environment
conda create --name AdvBench python=3.12
conda activate AdvBench

# Install requirements
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file in the project root directory with the following variables:

```env
OPENAI_API_KEY=your_openai_api_key
BASE_URL=your_base_url
```

### Additional Dependencies

```bash
pip install sentence-transformers
pip install openai
# Additional dependencies are automatically installed via requirements.txt
```

## 🤖 AdVocate Framework

AdVocate is a sophisticated multi-agent system designed for intelligent ad injection in LLM responses. It employs a two-stage approach and is the primary solution strategy in the AdvBench framework.

### Architecture

1. **Answer Agent**: Generates raw, unmodified responses to user queries
2. **Injector Agent**: Intelligently injects relevant product advertisements using RAG

### Key Features

- **Intelligent Product Matching**: Uses sentence transformers for semantic product selection
- **Context-Aware Injection**: Maintains conversation flow while inserting relevant ads
- **Configurable Strategies**: Multiple injection strategies (BASIC_GEN_INSERT, REFINE_GEN_INSERT)
- **RAG-Powered**: Leverages retrieval-augmented generation for product recommendations

### Workflow Stages

```python
# Stage 1: Raw Answer Generation
raw_answer = answer_agent.raw_answer(problem_list)

# Stage 2: Intelligent Ad Injection
injected_answer = injector_agent.inject_products(
    raw_answer, 
    query_type, 
    solution_name
)
```

## 💬 ChatBot Framework

ChatBot provides a comparative framework for analyzing different ad injection strategies in conversational AI systems. This serves as a competitor baseline in the AdvBench evaluation suite.

### Key Components

- **OpenAI Chat Session**: Integrated chat interface with ad injection capabilities
- **Parallel Processing**: Efficient batch processing using the ParallelProcessor base class
- **Configurable Demographics**: Support for targeted advertising based on user demographics
- **A/B Testing**: Built-in support for comparing different ad strategies

### Supported Strategies

- **Competitor Mode (`chi`)**: Aggressive ad injection strategy
- **Control Mode (`control`)**: Baseline/control group with minimal ad injection

## 🚀 Getting Started

### Quick Start

From the project root directory, you can run the main script to see the solutions in action:

```bash
python main.py
```

### Basic Import Setup

```python
from solutions.src.AdVocate.workflow import AdvocateWorkflow
from solutions.src.ChatBot.chatbotAdsWorkflow import ChatbotAdsWorkflow
```

**Note**: Make sure you're running from the project root directory to ensure proper module imports.

## 📝 Usage Examples

### AdVocate Workflow

```python
from solutions.src.AdVocate.workflow import AdvocateWorkflow

# Initialize AdVocate workflow with proper paths
advocate = AdvocateWorkflow(
    model_name="gpt-4o",
    product_list_path="benchmarking/dataset/product/products.json",
    rag_model=None  # Uses default all-MiniLM-L6-v2
)

# Run the workflow
problems = ["What's the best smartphone for photography?"]
results = advocate.run(
    problem_list=problems,
    query_type="QUERY_PROMPT_N_RESPONSE",  # Options: QUERY_PROMPT, QUERY_RESPONSE, QUERY_PROMPT_N_RESPONSE
    solution_name="REFINE_GEN_INSERT"      # Options: BASIC_GEN_INSERT, REFINE_GEN_INSERT
)

print(results)
```

### ChatBot Workflow

```python
from solutions.src.ChatBot.chatbotAdsWorkflow import ChatbotAdsWorkflow

# Initialize ChatBot workflow with proper paths
chatbot = ChatbotAdsWorkflow(
    product_list_path="benchmarking/dataset/product/products.json",
    topic_list_path="benchmarking/dataset/product/topics.json",
    model_name="gpt-4o"
)

# Run with competitor strategy
problems = ["I need a new laptop for work"]
results = chatbot.run(
    problem_list=problems,
    solution_name="chi",  # or "control"
    workers=4,
    batch_size=5
)

print(results)
```

### Parallel Processing Example

```python
# Large-scale evaluation with parallel processing
large_problem_set = [f"Query {i}" for i in range(100)]

results = chatbot.run(
    problem_list=large_problem_set,
    solution_name="chi",
    workers=8,           # 8 parallel workers
    batch_size=10,       # Process 10 items per batch
    max_retries=3,       # Retry failed requests
    timeout=180          # 3-minute timeout per request
)
```

## 🔗 Integration with AdvBench

The Solutions framework integrates seamlessly with the AdvBench benchmarking system:

```python
from benchmarking import AdvBench
from solutions.src.AdVocate.workflow import AdvocateWorkflow
from solutions.src.ChatBot.chatbotAdsWorkflow import ChatbotAdsWorkflow
from functools import partial

# Initialize comprehensive benchmark
adv_bench = AdvBench(
    data_sets=["MT-Human"],
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

# Run comprehensive evaluation
results = adv_bench.evaluate()
```

## 📊 Evaluation

### Query Types (AdVocate)

- `QUERY_PROMPT`: Inject ads in the prompt only
- `QUERY_RESPONSE`: Inject ads in the response only  
- `QUERY_PROMPT_N_RESPONSE`: Inject ads in both prompt and response

### Solution Names (AdVocate)

- `BASIC_GEN_INSERT`: Basic ad insertion strategy
- `REFINE_GEN_INSERT`: Refined ad insertion with improved context awareness

### Performance Metrics

Both frameworks support comprehensive evaluation through:

- **Response Quality Assessment**: Measuring the quality of generated responses
- **Ad Relevance Scoring**: Evaluating how well ads match the context
- **User Experience Impact**: Assessing the impact on user interaction
- **Conversion Rate Analysis**: Measuring advertising effectiveness
- **Multiple Evaluation Metrics**: Includes both comparative and quantitative evaluators
- **Comprehensive Reporting**: Generates Excel reports with detailed analysis

## 🔧 API Reference

### AdvocateWorkflow

```python
class AdvocateWorkflow:
    def __init__(
        self, 
        model_name: str = "gpt-4o",
        product_list_path: str = None,
        rag_model: Optional[SentenceTransformer] = None
    )
    
    def run(
        self, 
        problem_list: List[str], 
        query_type: str, 
        solution_name: str
    ) -> List[Dict]
    
    def help(self) -> None
```

### ChatbotAdsWorkflow

```python
class ChatbotAdsWorkflow(ParallelProcessor):
    def __init__(
        self,
        product_list_path: str,
        topic_list_path: str,
        model_name: str = "gpt-4o"
    )
    
    def run(
        self, 
        problem_list: List[str], 
        solution_name: str, 
        workers: int = None,
        batch_size: int = 5,
        max_retries: int = 2,
        timeout: int = 1800
    ) -> List[Dict[str, str]]
    
    def help(self) -> None
```

## 🎯 Best Practices

1. **Resource Management**: Use appropriate batch sizes and worker counts based on your system capabilities
2. **Error Handling**: Implement proper retry logic for production deployments
3. **Product Database**: Maintain up-to-date product lists for optimal ad relevance
4. **Path Configuration**: Always use paths relative to the project root directory
5. **Environment Variables**: Ensure proper API key configuration before running
6. **Evaluation**: Regular assessment using multiple metrics for comprehensive performance analysis
7. **Integration Testing**: Test solutions with the AdvBench framework for consistent results

## 🤝 Contributing

When contributing to the Solutions framework:

1. Follow the existing agent-based architecture patterns
2. Maintain compatibility with both workflow systems
3. Ensure integration with the AdvBench benchmarking framework
4. Include comprehensive tests for new features
5. Document API changes and new configuration options
6. Follow the project's coding standards and documentation format

## 📄 License

This project is part of the AdvBench framework and is licensed under the MIT License. See the LICENSE file in the project root for details. 
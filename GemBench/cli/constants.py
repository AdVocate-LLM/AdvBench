CHAT_DATASETS = ["MT-Human", "LM-Market"]
SEARCH_DATASET = "CA_Prod"
ALL_DATASETS = CHAT_DATASETS + [SEARCH_DATASET]

import os

try:
    from dotenv import load_dotenv
except ImportError:
    pass
else:
    load_dotenv()


DEFAULT_MODEL = os.environ.get("GEMBENCH_MODEL_NAME", "doubao-1-5-lite-32k-250115")
DEFAULT_EMBEDDING_MODEL = os.environ.get(
    "GEMBENCH_EMBEDDING_MODEL", "text-embedding-3-small"
)
DEFAULT_JUDGE_MODEL = os.environ.get("GEMBENCH_JUDGE_MODEL", "gpt-4.1-mini")

METHODS = {
    "ad-chat": {
        "name": "Ad-Chat",
        "description": "Prompt-based Ad-Chat baseline.",
        "tasks": ["inject", "generate", "select"],
    },
    "gi-r": {
        "name": "GI-R",
        "description": "Generate and inject with ad retrieval from the raw response.",
        "tasks": ["inject", "generate", "select"],
    },
    "gir-r": {
        "name": "GIR-R",
        "description": "Generate, inject, and rewrite with retrieval from the raw response.",
        "tasks": ["inject", "generate", "select"],
    },
    "gir-p": {
        "name": "GIR-P",
        "description": "Generate, inject, and rewrite with retrieval from the user prompt.",
        "tasks": ["inject", "generate", "select"],
    },
    "rag-adchat": {
        "name": "RAG-AdChat",
        "description": "Retrieval-augmented Ad-Chat baseline.",
        "tasks": ["inject", "generate", "select"],
    },
}

METHOD_ALIASES = {
    "all": "all",
    "adchat": "ad-chat",
    "ad-chat": "ad-chat",
    "chi": "ad-chat",
    "gi-r": "gi-r",
    "gir": "gi-r",
    "gir-r": "gir-r",
    "gir-p": "gir-p",
    "rag-adchat": "rag-adchat",
    "rag-ad-chat": "rag-adchat",
    "rag_adchat": "rag-adchat",
    "rag_ad_chat": "rag-adchat",
}

QUANT_MATRICES = [
    "has_ad",
    "local_flow",
    "global_coherence",
    "ad_transition_similarity",
    "ad_content_alignment",
    "in_token",
    "out_token",
    "price",
]
QUAL_MATRICES = [
    "accuracy_evaluation",
    "naturalness_evaluation",
    "personality_evaluation",
    "trust_evaluation",
    "notice_products_evaluation",
    "click_products_evaluation",
]
SELECT_MATRICES = ["product_selection_accuracy"]
ALL_MATRICES = QUANT_MATRICES + QUAL_MATRICES + SELECT_MATRICES

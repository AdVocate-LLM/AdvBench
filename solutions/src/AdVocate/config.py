# enum for productRAG
DEFAULT_RAG_MODEL = 'all-MiniLM-L6-v2'
ADS_START = "[[ADS_START]]"
ADS_END = "[[ADS_END]]"

# enum for injection methods
QUERY_PROMPT = "QUERY_PROMPT"
QUERY_RESPONSE = "QUERY_RESPONSE"
QUERY_PROMPT_N_RESPONSE = "QUERY_PROMPT_N_RESPONSE"

# enum for refine methods
REFINE_GEN_INSERT = 'REFINE_GEN_INSERT'
BASIC_GEN_INSERT = 'BASIC_GEN_INSERT'

# enum for injection score function
LINEAR_WEIGHT = "linear_weight"
LOG_WEIGHT = "log_weight"
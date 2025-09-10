import json
from pathlib import Path
import os

FILE_PATH = Path(__file__).absolute()
BASE_DIR = FILE_PATH.parent.parent.parent

# huggingface mirror
# os.environ["HF_ENDPOINT"] = "https://hf-mirror.com" # Uncomment this line if you want to use a specific Hugging Face mirror
# os.environ["HF_HOME"] = os.path.expanduser("~/hf_cache/")

REMOTE_URL = "https://api.openai.com/v1/chat/completions"
# Prefer environment variable to avoid hardcoding secrets
TOKEN = os.getenv("OPENAI_API_KEY", "your token here")
# DEFAULT_CHATAGENT_MODEL = "gpt-4o-mini"
# ADVANCED_CHATAGENT_MODEL = "gpt-4o"
DEFAULT_CHATAGENT_MODEL = "gpt-4.1-mini"
ADVANCED_CHATAGENT_MODEL = "gpt-4.1-mini"

# Responses API for reasoning models (o4/o3 families)
RESPONSES_URL = "https://api.openai.com/v1/responses"
# Models that should use Responses API and optionally support reasoning effort
REASONING_MODELS = {
    "o4",  # high‑end reasoning
    "o4-mini",
    "o3",
}
# Default reasoning effort for reasoning models; one of: low|medium|high
DEFAULT_REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT", "medium")

LOCAL_URL = "LOCAL_URL"
LOCAL_LLM = "LOCAL_LLM"
DEFAULT_EMBED_LOCAL_MODEL = "DEFAULT_EMBED_LOCAL_MODEL"

## for embedding model
DEFAULT_EMBED_ONLINE_MODEL = "BAAI/bge-base-en-v1.5"
EMBED_REMOTE_URL = "https://api.siliconflow.cn/v1/embeddings"
EMBED_TOKEN = "your embed token here"
SPLITTER_WINDOW_SIZE = 6
SPLITTER_CHUNK_SIZE = 2048

## for preprocessing
CRAWLER_BASE_URL = ""
CRAWLER_GOOGLE_SCHOLAR_SEND_TASK_URL = ""
DEFAULT_DATA_FETCHER_ENABLE_CACHE = True
CUT_WORD_LENGTH = 10
MD_TEXT_LENGTH = 20000
ARXIV_PROJECTION = (
    "_id, title, authors, detail_url, abstract, md_text, reference, detail_id, image"
)

## Iteration and paper pool limits
DEFAULT_ITERATION_LIMIT = 3
DEFAULT_PAPER_POOL_LIMIT = 1024

## llamaindex OpenAI
DEFAULT_LLAMAINDEX_OPENAI_MODEL = "gpt-4o"
# DEFAULT_OPENAI_MODEL = "gpt-3.5-turbo"
CHAT_AGENT_WORKERS = 4

## survey generation
COARSE_GRAINED_TOPK = 200
MIN_FILTERED_LIMIT = 150
NUM_PROCESS_LIMIT = 10

## fig retrieving
FIG_RETRIEVE_URL = ""
ENHANCED_FIG_RETRIEVE_URL = ""
FIG_CHUNK_SIZE = 8192
MATCH_TOPK = 3
FIG_RETRIEVE_Authorization = ""
FIG_RETRIEVE_TOKEN = ""

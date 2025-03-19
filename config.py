import os
from dotenv import load_dotenv


load_dotenv()

# Bot settings
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
ADMIN_NICKNAME = os.getenv("ADMIN_NICKNAME")
supported_languages = {"en", "de", "ru"}
messages_path = "./resources/bot_messages.json"
log_file_path = "./storage/logs/tg_bot.log"
uploads_path = "./storage/uploads/"
languages_db_path = "./storage/db/language_prefs.db"
users_data_db_path = "./storage/db/users_data.db"
sources_per_page = 7
cleanup_original = True  # Delete original files after processing
cleanup_markdown = False  # Delete markdown files after sending to user

# LLM settings
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT")
model_name = "Qwen/Qwen2.5-72B-Instruct"
prompts_dir = "./resources/prompts/"
max_tokens = 4096
temperature = 0.7
temperature_structured = 0.1

# Retrieval settings
embed_db_path = "./storage/db/faiss_index"
embed_model_device = "cuda:0"
retrieval_model_name = "HIT-TMG/KaLM-embedding-multilingual-mini-instruct-v1.5"
embed_dim = 896
chunk = 1_500
chunk_overlap = 300
top_k = 10
add_relative_queries = False  # Expand user's query with LLM-generated relative queries
relative_top_k = 3
use_reranking = False
rerank_model_name = "BAAI/bge-reranker-v2-m3"
rerank_top_k = 10

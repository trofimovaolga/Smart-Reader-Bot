import os
from typing import List, Optional

from pydantic import BaseModel
from FlagEmbedding import FlagReranker

from config import (
    prompts_dir,
    top_k,
    relative_top_k,
    use_reranking,
    rerank_top_k,
    rerank_model_name,
    embed_model_device,
    supported_languages,
)
from .llm import LLMService
from data.database_manager import DatabaseManager
from utils.logging_config import setup_logging
from utils.singleton import singleton


@singleton
class RAG:
    def __init__(self):
        self.llm = LLMService()
        self.prompt = self._load_prompts()
        self.db_manager = DatabaseManager()
        self.logger = setup_logging('RAG')
        
    def _load_prompts(self) -> str:
        prompt = dict()
        for lang in supported_languages:
            prompt_path = os.path.join(prompts_dir, f'rag_{lang}.md')
            if not os.path.exists(prompt_path):
                raise FileNotFoundError(f'Missing prompt {prompt_path}')
            with open(prompt_path, encoding='utf-8') as f:
                prompt[lang] = f.read()
        return prompt


    def _retrieve_documents(self, message: str, relative_questions: Optional[List], user_id: str) -> List:
        vector_store = self.db_manager.get_storage(user_id)
        all_docs = vector_store.similarity_search(message, k=top_k)

        if relative_questions:
            for msg in relative_questions:
                if msg != message:
                    docs = vector_store.similarity_search(msg, k=relative_top_k)
                    new_docs = [doc for doc in docs if doc not in all_docs]
                    all_docs.extend(new_docs)
        self.logger.info(f"Found {len(all_docs)} similar chunks for user {user_id}")
        return all_docs


    def _format_context(self, documents: List) -> tuple[str, str]:
        context = ""
        sources = []
        for doc in documents:
            file_name = doc.metadata.get("file_name", "")
            if file_name:
                file_name = f"/.../{file_name}"
            source = f"{doc.metadata['source']}{file_name}"
            if source not in sources:
                sources.append(source)
            context += f'Source: "{source}"\n\n{doc.page_content}\n\n'
        
        sources_str = f"Sources:\n{', '.join(sources)}\n\n" if sources else ""
        return context, sources_str


    def process(self, message: str, user_id: str, lang : str = 'en', relative_questions: Optional[List] = None) -> str:
        self.logger.info(f"Runing RAG for query {message} from user {user_id}")
        docs = self._retrieve_documents(message, relative_questions, user_id)

        if use_reranking:
            reranker = DocumentReranker()
            docs = reranker.rerank(message, docs)

        context, sources_str = self._format_context(docs)
        user_question = f"Question: {message}\nContext: {context}"
        response = self.llm.generate_text(self.prompt[lang], user_question)
        return sources_str + response
    


class DocumentReranker:
    def __init__(self):
        self.reranker = FlagReranker(rerank_model_name, use_fp16=True, device=embed_model_device)

    def rerank(self, message: str, documents: List) -> List:
        scores = [self.reranker.compute_score([message, doc.page_content]) for doc in documents]
        sorted_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:rerank_top_k]
        return [documents[idx] for idx in sorted_idx]



class RelativeQuestionsFormat(BaseModel):
    questions: List[str]


class QueryExpander:
    def __init__(self):
        self.llm = LLMService()
        self.prompt = self._load_prompts()

    def _load_prompts(self) -> str:
        prompt = dict()
        for lang in supported_languages:
            prompt_path = os.path.join(prompts_dir, f'expand_{lang}.md')
            if not os.path.exists(prompt_path):
                raise FileNotFoundError(f'Missing prompt {prompt_path}')
            with open(prompt_path, encoding='utf-8') as f:
                prompt[lang] = f.read()
        return prompt

    def expand_query(self, query: str, lang: str = 'en') -> List:
        self.llm.logger.info(f"Expanding message: {query}")
        response = self.llm.generate_structured(
            prompt=self.prompt[lang],
            message=query,
            schema=RelativeQuestionsFormat
        )
        self.llm.logger.debug(f"Expanded questions: {response.questions}")
        return response.questions
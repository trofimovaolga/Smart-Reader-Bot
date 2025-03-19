import os
import torch
import faiss
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_huggingface import HuggingFaceEmbeddings
from FlagEmbedding import FlagReranker

from config import (
    embed_model_device,
    retrieval_model_name,
    rerank_model_name,
    chunk,
    use_reranking,
    embed_dim,
    embed_db_path,
)
from utils.logging_config import setup_logging
from utils.singleton import singleton



@singleton
class DatabaseManager:
    """
    Manages the database operations including storing and retrieving documents. 
    Utilizes FAISS for vector storage and HuggingFaceEmbeddings for generating embeddings. 
    Optionally uses a reranker for improving retrieval quality. 
    Implements a singleton pattern to ensure a single instance of the database manager. 
    """
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=retrieval_model_name, 
            model_kwargs={'device': embed_model_device},
        )
        if use_reranking:
            self.reranker = FlagReranker(rerank_model_name, use_fp16=True, device=embed_model_device)
        self.logger = setup_logging('DatabaseManager')
    

    def _get_user_dir(self, user_id: str) -> str:
        """Get the directory for a specific user's FAISS index."""
        user_dir = os.path.join(embed_db_path, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        return user_dir
    

    def _get_index(self) -> str:
        index_name = f"faiss-{retrieval_model_name.split('/')[-1]}-{chunk}".lower().replace('.', '')
        return index_name
    
    
    def get_storage(self, user_id: str):
        """Create or retrieve storage for a user"""
        index_name = self._get_index()
        user_dir = self._get_user_dir(user_id)
        index_path = os.path.join(user_dir, index_name)
        if os.path.exists(index_path):
            return FAISS.load_local(index_path, self.embeddings, allow_dangerous_deserialization=True)
        else:
            vector_storage = FAISS(
                embedding_function=self.embeddings,
                index=faiss.IndexFlatL2(embed_dim),
                docstore=InMemoryDocstore(),
                index_to_docstore_id={},
            )
            vector_storage.save_local(index_path)

            return vector_storage


    def add_docs(self, chunks: list[Document], user_id: str):
        """Add embeddings to user's storage"""
        self.logger.debug(f"Looking for vector storage for user {user_id}")
        vector_storage = self.get_storage(user_id)
        self.logger.debug(f"Created/found vector storage for user {user_id}")

        self.embeddings.model_kwargs['device'] = embed_model_device
        try:
            vector_storage.add_documents(documents=filter_complex_metadata(chunks))
        except ValueError as e:
            self.logger.error(f"Failed to add document to database: {e}")
            return
        # TODO: check that there is always a source in the chunk
        
        user_dir = self._get_user_dir(user_id)
        index_path = os.path.join(user_dir, self._get_index())
        vector_storage.save_local(index_path)
        self.embeddings.model_kwargs['device'] = 'cpu'
        torch.cuda.empty_cache()

        self.logger.info(f"Added {len(chunks)} items to {user_id}'s storage.")
        return True


    def get_users_docs(self, user_id: str):
        """Retrieves all documents for a given user from the database"""
        self.logger.debug(f"Looking for vector storage for user {user_id}")
        vector_storage = self.get_storage(user_id)
        self.logger.debug(f"Created/found vector storage for user {user_id}")

        all_data = list(vector_storage.docstore._dict.values())
        all_sources = set(data.metadata['source'] for data in all_data if "source" in data.metadata)
        all_sources = sorted(all_sources)

        self.logger.debug(f"Found {len(all_sources)} saved sources for user {user_id}")
        return all_sources


    def delete_doc(self, source: str, user_id: str):
        """Delete documents from user's storage that match the given source name"""
        vector_storage = self.get_storage(user_id)
        all_data = vector_storage.docstore._dict
        src_dict = dict()
        for k, v in all_data.items():
            if "source" in v.metadata:
                src_dict[k] = v.metadata['source']

        ids_to_delete = [
            doc_id for doc_id, src in src_dict.items() if src.startswith(source)
        ]

        if not ids_to_delete:
            self.logger.info(f"No documents found with source '{source}' for user {user_id}.")
            return

        vector_storage.delete(ids=ids_to_delete)
        user_dir = self._get_user_dir(user_id)
        index_path = os.path.join(user_dir, self._get_index())
        vector_storage.save_local(index_path)
        # TODO: also delete *.md files if exist

        self.logger.info(f"Deleted {len(ids_to_delete)} documents with source '{source}' from {user_id}'s storage.")

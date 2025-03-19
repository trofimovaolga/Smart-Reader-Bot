import os
from typing import List, Optional
from markitdown import MarkItDown
from markitdown._markitdown import UnsupportedFormatException
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    chunk,
    chunk_overlap
)
from data.utils import clean_md
from data.database_manager import DatabaseManager



async def process_file(
        file_path: str, 
        user_id: str, 
        source: Optional[str] = None,
        cleanup_original: bool = True,
        cleanup_markdown: bool = True,
    ) -> bool:
    """
    Extract text from user's file and save it to database.
    Args:
        file_path: Path to the file to process
        user_id: Telegram ID of the user who owns the file
        source: Source name to use in metadata (defaults to filename)
        cleanup_original: Whether to delete the original file after processing
        cleanup_markdown: Whether to delete the generated markdown file
    Returns:
        success_status
    """
    db_manager = DatabaseManager()
    db_manager.logger.info(f'Processing file from user {user_id}.')

    if not os.path.exists(file_path):
        db_manager.logger.error(f'File not found: {file_path}')
        return False
    
    if source is None:
        source = os.path.basename(file_path)
    
    md_file = f'{os.path.splitext(file_path)[0]}.md'

    try:
        markdown_result = await convert_to_markdown(file_path, user_id, source)
        if markdown_result is None:
            return False

        with open(md_file, 'w') as out:
            out.write(markdown_result)
        db_manager.logger.info(f'File from user {user_id} converted to md format.')

        docs = [Document(page_content=markdown_result, metadata={'source': source})]

        chunks_added = await add_docs_to_database(docs, user_id)
        if not chunks_added:
            return False
        db_manager.logger.info(f'{chunks_added} chunks from {source} added to user {user_id} database.')

        if cleanup_original:
            os.remove(file_path)
            db_manager.logger.info(f'File {source} from user {user_id} deleted from local directory.')
        
        if cleanup_markdown and os.path.exists(md_file):
            os.remove(md_file)
            db_manager.logger.info(f'Generated markdown file {md_file} deleted from local directory.')
        return True
    
    except UnsupportedFormatException:
        db_manager.logger.exception(f'File {source} from user {user_id} has unsupported format.')
        return False
    except Exception as e:
        db_manager.logger.exception(f'Unexpected error processing file {source}: {str(e)}')
        return False
    

async def convert_to_markdown(file_path: str, user_id: str, source: str) -> Optional[str]:
    """Convert a file to Markdown format.""" 
    db_manager = DatabaseManager()   
    try:
        if os.path.splitext(file_path)[-1].lower() in ['.txt', '.md']:
            with open(file_path) as f:
                markdown_result = f.read()
        else:
            md = MarkItDown()
            markdown_result = md.convert(file_path).text_content
            if not markdown_result:
                db_manager.logger.error(f'No text found in {source}, user: {user_id}')
                return
        
        markdown_result = clean_md(markdown_result)
        return markdown_result

    except UnsupportedFormatException:
        db_manager.logger.exception(f'File {source} from user {user_id} has unsupported format.')
        return
    except Exception as e:
        db_manager.logger.exception(f'Unexpected error processing file {source}, user: {user_id}: {str(e)}')
        return


async def add_docs_to_database(documents: List[Document], user_id: str) -> Optional[int]:
    """
    Split text to chunks and add the chunks to user's databse.
    Args:
        documents: List of Document objects to process
        user_id: Telegram ID of the user who owns the documents
    Returns:
        Number of chunks added to the database (if added)
    """
    db_manager = DatabaseManager()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk,
        chunk_overlap=chunk_overlap,
        separators=["\n", "."],
    )
    chunks = text_splitter.split_documents(documents)
    db_manager.logger.info(f'Text from user {user_id} split into {len(chunks)} chunks.')
    
    
    added_ok = db_manager.add_docs(chunks, user_id)
    if added_ok:
        return len(chunks)
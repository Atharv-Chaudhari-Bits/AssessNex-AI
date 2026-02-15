"""
RAG (Retrieval-Augmented Generation) module for subject concepts.
Stores and retrieves relevant context for question generation.
"""

import os
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime

from backend.app.utils import get_logger

logger = get_logger(__name__)

# Try to import LangChain and vector store dependencies
try:
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.vectorstores import Chroma
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
    from langchain.schema import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain not installed. RAG pipeline will be disabled.")


class SubjectRAG:
    """
    RAG pipeline for storing and retrieving subject-specific concepts.
    Uses vector embeddings to find relevant context for question generation.
    """
    
    def __init__(self, persist_directory: str = "./data/vectorstore"):
        """
        Initialize the RAG pipeline.
        
        Args:
            persist_directory: Directory to store vector embeddings
        """
        self.persist_directory = persist_directory
        self.embeddings = None
        self.vectorstores = {}  # subject -> vectorstore
        self.text_splitter = None
        
        if LANGCHAIN_AVAILABLE:
            self._initialize_embeddings()
            self._initialize_text_splitter()
            self._load_existing_vectorstores()
    
    def _initialize_embeddings(self):
        """Initialize the embedding model."""
        try:
            # Use a good general-purpose embedding model
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info("Embeddings model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {str(e)}")
    
    def _initialize_text_splitter(self):
        """Initialize text splitter for chunking documents."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def _load_existing_vectorstores(self):
        """Load existing vector stores from disk."""
        if not os.path.exists(self.persist_directory):
            os.makedirs(self.persist_directory, exist_ok=True)
            return
        
        try:
            # Look for subject directories
            for item in os.listdir(self.persist_directory):
                subject_path = os.path.join(self.persist_directory, item)
                if os.path.isdir(subject_path):
                    try:
                        vectorstore = Chroma(
                            persist_directory=subject_path,
                            embedding_function=self.embeddings
                        )
                        self.vectorstores[item] = vectorstore
                        logger.info(f"Loaded vectorstore for subject: {item}")
                    except Exception as e:
                        logger.warning(f"Failed to load vectorstore for {item}: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading vectorstores: {str(e)}")
    
    def _get_subject_path(self, subject: str) -> str:
        """Get the path for a subject's vector store."""
        # Sanitize subject name for filesystem
        safe_name = subject.lower().replace(' ', '_').replace('-', '_')
        return os.path.join(self.persist_directory, safe_name)
    
    def add_subject_content(
        self, 
        subject: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "manual"
    ) -> bool:
        """
        Add content for a subject to the vector store.
        
        Args:
            subject: Subject name (e.g., "Machine Learning")
            content: Text content to add
            metadata: Additional metadata
            source: Source of the content (manual, textbook, notes, etc.)
        
        Returns:
            bool: True if successful
        """
        if not LANGCHAIN_AVAILABLE or not self.embeddings:
            logger.error("LangChain or embeddings not available")
            return False
        
        try:
            # Create metadata
            doc_metadata = {
                "subject": subject,
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "content_hash": hashlib.md5(content.encode()).hexdigest()[:8]
            }
            if metadata:
                doc_metadata.update(metadata)
            
            # Split content into chunks
            chunks = self.text_splitter.split_text(content)
            
            # Create documents
            documents = [
                Document(
                    page_content=chunk,
                    metadata=doc_metadata
                )
                for chunk in chunks
            ]
            
            # Get or create vectorstore for subject
            subject_path = self._get_subject_path(subject)
            
            if subject in self.vectorstores:
                # Add to existing store
                self.vectorstores[subject].add_documents(documents)
                self.vectorstores[subject].persist()
            else:
                # Create new store
                vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=subject_path
                )
                vectorstore.persist()
                self.vectorstores[subject] = vectorstore
            
            logger.info(f"Added {len(chunks)} chunks for subject: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding subject content: {str(e)}")
            return False
    
    def add_subject_document(
        self,
        subject: str,
        file_path: str,
        file_type: str = "auto"
    ) -> bool:
        """
        Add content from a document file.
        
        Args:
            subject: Subject name
            file_path: Path to the document
            file_type: File type (pdf, docx, txt) or "auto" for auto-detection
        
        Returns:
            bool: True if successful
        """
        if not LANGCHAIN_AVAILABLE:
            logger.error("LangChain not available")
            return False
        
        try:
            # Determine file type
            if file_type == "auto":
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.pdf':
                    file_type = 'pdf'
                elif ext in ['.docx', '.doc']:
                    file_type = 'docx'
                else:
                    file_type = 'txt'
            
            # Load document based on type
            if file_type == 'pdf':
                loader = PyPDFLoader(file_path)
            elif file_type == 'docx':
                loader = Docx2txtLoader(file_path)
            else:
                loader = TextLoader(file_path, encoding='utf-8')
            
            documents = loader.load()
            
            # Add metadata
            for doc in documents:
                doc.metadata['subject'] = subject
                doc.metadata['source'] = os.path.basename(file_path)
                doc.metadata['timestamp'] = datetime.now().isoformat()
            
            # Split documents
            split_docs = self.text_splitter.split_documents(documents)
            
            # Get or create vectorstore
            subject_path = self._get_subject_path(subject)
            
            if subject in self.vectorstores:
                self.vectorstores[subject].add_documents(split_docs)
                self.vectorstores[subject].persist()
            else:
                vectorstore = Chroma.from_documents(
                    documents=split_docs,
                    embedding=self.embeddings,
                    persist_directory=subject_path
                )
                vectorstore.persist()
                self.vectorstores[subject] = vectorstore
            
            logger.info(f"Added document {file_path} for subject: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            return False
    
    def query_subject(
        self,
        subject: str,
        query: str,
        k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Query a subject's vector store for relevant context.
        
        Args:
            subject: Subject name
            query: Query text
            k: Number of results to return
            score_threshold: Minimum similarity score (0-1)
        
        Returns:
            List of relevant contexts with scores
        """
        if not LANGCHAIN_AVAILABLE:
            logger.error("LangChain not available")
            return []
        
        if subject not in self.vectorstores:
            logger.warning(f"No vectorstore found for subject: {subject}")
            return []
        
        try:
            # Perform similarity search
            if score_threshold:
                docs_with_scores = self.vectorstores[subject].similarity_search_with_relevance_scores(
                    query, k=k, score_threshold=score_threshold
                )
                results = [
                    {
                        "content": doc.page_content,
                        "score": score,
                        "metadata": doc.metadata
                    }
                    for doc, score in docs_with_scores
                ]
            else:
                docs = self.vectorstores[subject].similarity_search(query, k=k)
                results = [
                    {
                        "content": doc.page_content,
                        "score": 1.0,  # No score when using similarity_search
                        "metadata": doc.metadata
                    }
                    for doc in docs
                ]
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying subject: {str(e)}")
            return []
    
    def query_all_subjects(
        self,
        query: str,
        subjects: Optional[List[str]] = None,
        k_per_subject: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Query multiple subjects and combine results.
        
        Args:
            query: Query text
            subjects: List of subjects to query (None for all)
            k_per_subject: Results per subject
        
        Returns:
            Combined list of relevant contexts
        """
        if subjects is None:
            subjects = list(self.vectorstores.keys())
        
        all_results = []
        for subject in subjects:
            results = self.query_subject(subject, query, k=k_per_subject)
            all_results.extend(results)
        
        # Sort by score (highest first)
        all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return all_results
    
    def get_subject_summary(self, subject: str, max_chunks: int = 5) -> str:
        """
        Get a summary of a subject's content.
        
        Args:
            subject: Subject name
            max_chunks: Maximum number of chunks to include
        
        Returns:
            Summarized content
        """
        if subject not in self.vectorstores:
            return f"No content found for subject: {subject}"
        
        try:
            # Get all documents (limited)
            collection = self.vectorstores[subject]._collection
            all_docs = collection.get(limit=max_chunks)
            
            if not all_docs or not all_docs.get('documents'):
                return f"No documents found for subject: {subject}"
            
            summary = f"## {subject} - Content Summary\n\n"
            for i, doc in enumerate(all_docs['documents'][:max_chunks]):
                summary += f"### Excerpt {i+1}\n{doc[:300]}...\n\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting subject summary: {str(e)}")
            return f"Error retrieving summary for {subject}"
    
    def delete_subject(self, subject: str) -> bool:
        """
        Delete a subject's vector store.
        
        Args:
            subject: Subject name
        
        Returns:
            bool: True if successful
        """
        import shutil
        
        if subject not in self.vectorstores:
            return False
        
        try:
            subject_path = self._get_subject_path(subject)
            if os.path.exists(subject_path):
                shutil.rmtree(subject_path)
            
            del self.vectorstores[subject]
            logger.info(f"Deleted vectorstore for subject: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting subject: {str(e)}")
            return False
    
    def list_subjects(self) -> List[str]:
        """List all available subjects."""
        return list(self.vectorstores.keys())
    
    def get_stats(self, subject: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about the vector stores.
        
        Args:
            subject: Optional specific subject
        
        Returns:
            Statistics dictionary
        """
        stats = {
            "total_subjects": len(self.vectorstores),
            "subjects": {}
        }
        
        try:
            for subj, store in self.vectorstores.items():
                if subject and subj != subject:
                    continue
                
                collection = store._collection
                count = collection.count()
                
                stats["subjects"][subj] = {
                    "chunk_count": count,
                    "persist_directory": self._get_subject_path(subj)
                }
                
                if subject:
                    # Get sample of content
                    sample_docs = collection.get(limit=3)
                    stats["subjects"][subj]["samples"] = [
                        doc[:200] + "..." 
                        for doc in (sample_docs.get('documents') or [])
                    ]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return stats


# Singleton instance
_rag_instance: Optional[SubjectRAG] = None


def get_rag() -> SubjectRAG:
    """Get or create the RAG instance."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = SubjectRAG()
    return _rag_instance
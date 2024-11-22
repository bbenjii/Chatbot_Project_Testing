# app/services/vector_service.py
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv

from datetime import datetime, timezone
import numpy as np
from bson import ObjectId
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker

from langchain_openai import AzureOpenAIEmbeddings

from app.config import settings
from app.models.vector_chunk import VectorChunk
from app.core.exceptions import AppException
from app.core.database import Database

logger = logging.getLogger(__name__)
load_dotenv()  # Load environment variables


class VectorService:
    def __init__(self):
        self.db = Database.get_db()
        self.vector_model = VectorChunk(self.db)
        # Initialize Azure OpenAI embeddings
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT"),
            # openai_api_key=settings.AZURE_OPENAI_KEY,
            # deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            # chunk_size=1000  # Adjust based on your needs
        )

        # Configure text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

        self.semantic_text_splitter = SemanticChunker(
            embeddings=self.embeddings,
            breakpoint_threshold_amount=95
        )

    async def process_document(
            self,
            document_id: str,
            user_id: str,
            text_content: str,
            metadata: Optional[Dict[str, Any]] = None
    ) -> List[ObjectId]:
        """Process a document and store its vector embeddings."""
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(text_content)

            # Generate embeddings for all chunks
            embeddings = await self._generate_embeddings_batch(chunks)

            # Store chunks and their embeddings
            chunk_ids = []
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_metadata = {
                    "document_id": document_id,
                    "chunk_index": idx,
                    **(metadata or {})
                }

                chunk_id = await self.vector_model.create_chunk(
                    document_id=document_id,
                    user_id=user_id,
                    chunk_index=idx,
                    text_content=chunk,
                    vector_embedding=embedding,
                    metadata=chunk_metadata
                )
                chunk_ids.append(chunk_id)

            logger.info(f"Processed document {document_id} into {len(chunks)} chunks")
            return chunk_ids

        except Exception as e:
            logger.error(f"Error processing document: {e}")
            raise AppException(f"Failed to process document: {str(e)}")

    async def search_similar(
            self,
            user_id: str,
            query: str,
            limit: int = 5,
            min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks using vector similarity."""
        try:
            # Generate embedding for the query
            query_embedding = await self._generate_embedding(query)

            # Search for similar chunks
            results = await self.vector_model.find_similar_chunks(
                user_id=user_id,
                vector=query_embedding,
                limit=limit
            )

            # Filter results by similarity threshold
            filtered_results = []
            for result in results:
                similarity = self._calculate_similarity(
                    query_embedding,
                    result['vector_embedding']
                )
                if similarity >= min_similarity:
                    result['similarity'] = float(similarity)
                    filtered_results.append(result)

            return filtered_results

        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            raise AppException(f"Failed to perform similarity search: {str(e)}")

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            embedding = await self.embeddings.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def _generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        try:
            embeddings = await self.embeddings.aembed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise

    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)

            # Compute cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            return dot_product / (norm1 * norm2)

        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            raise

    async def delete_document_vectors(self, document_id: str, user_id: str) -> int:
        """Delete all vector chunks for a document."""
        try:
            count = await self.vector_model.delete_many({
                'document_id': ObjectId(document_id),
                'user_id': ObjectId(user_id)
            })
            logger.info(f"Deleted {count} vector chunks for document {document_id}")
            return count
        except Exception as e:
            logger.error(f"Error deleting document vectors: {e}")
            raise AppException(f"Failed to delete document vectors: {str(e)}")

    async def get_document_chunks(
            self,
            document_id: str,
            user_id: str
    ) -> List[Dict[str, Any]]:
        """Get all chunks for a document."""
        try:
            chunks = await self.vector_model.find_many({
                'document_id': ObjectId(document_id),
                'user_id': ObjectId(user_id)
            }, sort=[('chunk_index', 1)])
            return chunks
        except Exception as e:
            logger.error(f"Error fetching document chunks: {e}")
            raise AppException(f"Failed to fetch document chunks: {str(e)}")

    async def reprocess_document(
            self,
            document_id: str,
            user_id: str,
            text_content: str,
            metadata: Optional[Dict[str, Any]] = None
    ) -> List[ObjectId]:
        """Reprocess a document by deleting existing vectors and creating new ones."""
        try:
            # Delete existing vectors
            await self.delete_document_vectors(document_id, user_id)

            # Process document again
            return await self.process_document(
                document_id=document_id,
                user_id=user_id,
                text_content=text_content,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error reprocessing document: {e}")
            raise AppException(f"Failed to reprocess document: {str(e)}")
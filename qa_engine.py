"""
Question Answering Engine
==========================
Implements the RAG (Retrieval-Augmented Generation) pipeline.

Pipeline:
PDF Text → Chunks → Embeddings → FAISS Vector Store
→ User Question → Similar Chunk Retrieval → AI Answer Generation

Uses free Groq API for fast LLM inference.
"""
from dotenv import load_dotenv
load_dotenv()
import os
from typing import List, Optional

# LangChain components
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

# Groq for fast, free LLM inference
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


class QAEngine:
    """
    Manages the vector store and answers questions using RAG.
    
    RAG = Retrieval-Augmented Generation
    - Instead of asking the AI to remember everything, we:
    1. Find the most relevant PDF sections for each question
    2. Give those sections to the AI as context
    3. Ask the AI to answer ONLY based on that context
    
    This makes answers much more accurate and grounded in the PDF!
    """

    def __init__(self):
        self.vector_store = None
        self._is_ready = False

        # Initialize Groq client if API key is available
        groq_key = os.getenv('GROQ_API_KEY')
        if GROQ_AVAILABLE and groq_key:
            self.groq_client = Groq(api_key=groq_key)
            self.model = os.getenv('GROQ_MODEL')

            if not self.model:
                raise ValueError("GROQ_MODEL not set in .env file")
        else:
            self.groq_client = None
            self.model = None

        # Use HuggingFace embeddings (free, runs locally)
        # This converts text into numerical vectors for similarity search
        print("Loading embedding model... (first time may take a moment)")
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",  # Small, fast, good quality
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
        
        except Exception as e:
            print(f"Warning: Could not load embedding model: {e}")
            self.embeddings = None


    def build_vector_store(self, chunks: List[str]) -> bool:
        """
        Build a FAISS vector store from text chunks.
        
        FAISS = Facebook AI Similarity Search
        It's a library for efficient similarity search in high-dimensional spaces.
        
        Args:
            chunks: List of text strings to index
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.embeddings:
                print("Embeddings not available, using simple keyword search")
                self._chunks = chunks
                self._is_ready = True
                return True

            # Convert chunks to LangChain Document objects
            documents = [
                Document(page_content=chunk, metadata={"chunk_id": i})
                for i, chunk in enumerate(chunks)
            ]

            # Create FAISS vector store from documents
            # This converts all text chunks to embedding vectors
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
            self._is_ready = True
            self._chunks = chunks
            print(f"Vector store built with {len(chunks)} chunks")
            return True

        except Exception as e:
            print(f"Vector store error: {e}")
            # Fall back to simple storage
            self._chunks = chunks
            self._is_ready = True
            return False

    def answer_question(self, question: str) -> str:
        """
        Answer a question using the RAG pipeline.
        
        Steps:
        1. Find relevant chunks using vector similarity search
        2. Build a prompt with the question and relevant context
        3. Get an answer from the LLM
        4. Return the answer
        """
        try:
            # Step 1: Retrieve relevant context
            context = self._retrieve_context(question)

            if not context:
                return "I couldn't find relevant information in the PDF to answer this question."

            # Step 2: Generate answer using LLM
            answer = self._generate_answer(question, context)
            return answer

        except Exception as e:
            return f"Error generating answer: {str(e)}"

    def _retrieve_context(self, question: str, k: int = 4) -> str:
        """
        Retrieve the most relevant text chunks for a question.
        
        Args:
            question: The user's question
            k: Number of chunks to retrieve
            
        Returns:
            Combined relevant text
        """
        try:
            if self.vector_store and self.embeddings:
                # Use FAISS similarity search (best method)
                docs = self.vector_store.similarity_search(question, k=k)
                context_parts = [doc.page_content for doc in docs]
            else:
                # Fallback: simple keyword matching
                context_parts = self._keyword_search(question, k)

            return "\n\n---\n\n".join(context_parts)

        except Exception as e:
            print(f"Retrieval error: {e}")
            # Last resort fallback
            if hasattr(self, '_chunks') and self._chunks:
                return "\n\n".join(self._chunks[:3])
            return ""

    def _keyword_search(self, question: str, k: int = 4) -> List[str]:
        """
        Simple keyword-based search fallback when FAISS is unavailable.
        """
        if not hasattr(self, '_chunks') or not self._chunks:
            return []

        # Score each chunk by how many question words it contains
        question_words = set(question.lower().split())
        scored_chunks = []

        for chunk in self._chunks:
            chunk_words = set(chunk.lower().split())
            # Score = number of matching words
            score = len(question_words.intersection(chunk_words))
            scored_chunks.append((score, chunk))

        # Sort by score (highest first) and return top k
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in scored_chunks[:k] if score > 0]

    def _generate_answer(self, question: str, context: str) -> str:
        """
        Generate an answer using the LLM with the retrieved context.
        
        The prompt is carefully crafted to:
        - Make the AI answer ONLY from the provided context
        - Return a specific message if the answer isn't in the PDF
        - Keep answers clear and helpful
        """
        # Build the prompt
        prompt = f"""You are a helpful study assistant. Answer the user's question based ONLY on the provided PDF content below.

IMPORTANT RULES:
- Answer ONLY using the information in the PDF content below
- If the answer is not found in the PDF content, respond with EXACTLY: "This information is not present in the uploaded PDF."
- Be clear, concise, and helpful
- Do not make up or infer information not explicitly stated in the PDF

PDF Content:
{context}

User Question: {question}

Answer:"""

        # Try Groq first (fast and free)
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a precise study assistant that answers questions strictly based on provided PDF content."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=500,
                    temperature=0.1  # Low temperature = more focused, less creative
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"Groq API error: {e}")

        # Fallback: Try Gemini
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            try:
                return self._gemini_generate(prompt, gemini_key)
            except Exception as e:
                print(f"Gemini API error: {e}")

        # Last resort: Return a message asking user to configure API
        return ("I found relevant content in your PDF, but I need an AI API to generate a proper answer. "
                "Please add your GROQ_API_KEY to the .env file. "
                f"Relevant PDF excerpt: {context[:300]}...")

    def _gemini_generate(self, prompt: str, api_key: str) -> str:
        """Generate answer using Google Gemini API as fallback."""
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 500, "temperature": 0.1}
        }
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()
        if 'candidates' in data:
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            return "Gemini API failed: " + str(data)
    def is_ready(self) -> bool:
        """Check if the QA engine has a vector store ready."""
        return self._is_ready

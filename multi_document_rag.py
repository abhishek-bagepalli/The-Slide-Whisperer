import os
import shutil
from typing import List, Dict
from document_parser import process_document
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

class MultiDocumentRAG:
    def __init__(self, 
                 persist_directory: str = "./chroma_db",
                 chunk_size: int = 3000,
                 chunk_overlap: int = 200,
                 force_recreate: bool = False):
        """
        Initialize the MultiDocumentRAG system.
        
        Args:
            persist_directory (str): Directory to store the vector database
            chunk_size (int): Size of text chunks for splitting documents
            chunk_overlap (int): Overlap between chunks
            force_recreate (bool): Whether to force recreation of the database even if it exists
        """
        self.persist_directory = persist_directory
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Clear existing vector store if it exists and force_recreate is True
        if os.path.exists(persist_directory) and force_recreate:
            try:
                print(f"Clearing existing vector store at {persist_directory}")
                shutil.rmtree(persist_directory)
            except PermissionError:
                print(f"Warning: Could not delete existing database at {persist_directory}. It may be in use.")
                print("Using existing database instead.")
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Initialize vector store
        self.vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings
        )
        
        # Initialize LLM and QA chain
        self.llm = ChatOpenAI(
            temperature=0,
            model_name="gpt-3.5-turbo"
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 3}
            )
        )

    def __del__(self):
        """Cleanup when the object is destroyed"""
        try:
            if hasattr(self, 'vectorstore'):
                # In newer versions of ChromaDB, persistence is handled automatically
                pass
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")

    def process_documents(self, document_paths: List[str]) -> None:
        """
        Process multiple documents and add them to the vector store.
        
        Args:
            document_paths (List[str]): List of paths to documents
        """
        total_chunks = 0
        for doc_path in document_paths:
            print(f"\nProcessing document: {doc_path}")
            
            # Process document using existing parser
            json_result = process_document(doc_path, save_json=True)
            
            # Extract text from all pages
            text_content = ""
            for page in json_result[0]['pages']:
                text_content += page['text'] + "\n\n"
            
            # Split text into chunks
            texts = self.text_splitter.split_text(text_content)
            print(f"Generated {len(texts)} chunks from {doc_path}")
            total_chunks += len(texts)
            
            # Create documents with metadata
            documents = [
                Document(
                    page_content=t,
                    metadata={
                        "source": doc_path,
                        "chunk_id": f"{os.path.basename(doc_path)}_{i}"
                    }
                ) for i, t in enumerate(texts)
            ]
            
            # Add to vector store
            self.vectorstore.add_documents(documents)
            print(f"Added {len(documents)} chunks to vector store from {doc_path}")
            
            # In newer versions of ChromaDB, persistence is handled automatically
            # No need to call persist() explicitly
        
        # Get total document count in vector store
        collection = self.vectorstore._collection
        total_docs = collection.count()
        print(f"\nVector store statistics:")
        print(f"Total documents processed: {len(document_paths)}")
        print(f"Total chunks created: {total_chunks}")
        print(f"Total chunks in vector store: {total_docs}")

    def query(self, question: str) -> Dict:
        """
        Query the RAG system with a question.
        
        Args:
            question (str): The question to ask
            
        Returns:
            Dict: Response containing the answer and source documents
        """
        print("\nQuerying vector store...")
        response = self.qa_chain.invoke(question)
        
        # Add source documents to response
        source_documents = self.vectorstore.similarity_search(question, k=3)
        sources = [doc.metadata["source"] for doc in source_documents]
        print("Sources used for answer:", set(sources))
        
        return response

    def get_exact_content(self, query: str, k: int = 3) -> List[Dict]:
        """
        Retrieve exact content from documents without LLM processing.
        
        Args:
            query (str): The search query
            k (int): Number of chunks to retrieve
            
        Returns:
            List[Dict]: List of dictionaries containing the exact content and metadata
        """
        # Get similar documents directly from vector store
        documents = self.vectorstore.similarity_search(query, k=k)
        
        # Format the results and ensure uniqueness
        seen_contents = set()
        results = []
        for doc in documents:
            content = doc.page_content
            # Only add if we haven't seen this content before
            if content not in seen_contents:
                seen_contents.add(content)
                results.append({
                    "content": content,
                    "source": doc.metadata["source"],
                    "chunk_id": doc.metadata["chunk_id"]
                })
            
        return results

    def get_cleaned_content(self, query: str, k: int = 3) -> List[Dict]:
        """
        Retrieve content from documents and clean it up while preserving meaning.
        
        Args:
            query (str): The search query
            k (int): Number of chunks to retrieve
            
        Returns:
            List[Dict]: List of dictionaries containing the cleaned content and metadata
        """
        # Get similar documents directly from vector store
        documents = self.vectorstore.similarity_search(query, k=k)
        
        # Format the results and ensure uniqueness
        seen_contents = set()
        results = []
        
        for doc in documents:
            content = doc.page_content
            # Only process if we haven't seen this content before
            if content not in seen_contents:
                seen_contents.add(content)
                
                # Use LLM to clean up the content while preserving meaning
                cleanup_prompt = f"""Clean up the following text while preserving its exact meaning. 
                Only fix formatting issues, remove extra whitespace, and fix any obvious typos.
                Do not paraphrase or change the meaning in any way.
                
                Text to clean up:
                {content}
                
                Cleaned text:"""
                
                cleaned_content = self.llm.invoke(cleanup_prompt).content
                
                results.append({
                    "content": cleaned_content,
                    "source": doc.metadata["source"],
                    "chunk_id": doc.metadata["chunk_id"]
                })
            
        return results

def query_documents(questions, document_paths, rag, exact_content: bool = False, cleaned_content: bool = False):
    # rag = MultiDocumentRAG()
    
    # Process documents
    # document_paths = [
    #     "./docs/Airbnb Case.pdf"
    # ]

    responses = []
    
    if document_paths:
        for question in questions:
            if cleaned_content:
                response = rag.get_cleaned_content(question)
                print(f"\nQuestion: {question}")
                print("Cleaned content from documents:")
                for i, result in enumerate(response, 1):
                    print(f"\nChunk {i}:")
                    print(f"Source: {result['source']}")
                    print(f"Content: {result['content']}")
                responses.append(response)
            elif exact_content:
                response = rag.get_exact_content(question)
                print(f"\nQuestion: {question}")
                print("Exact content from documents:")
                for i, result in enumerate(response, 1):
                    print(f"\nChunk {i}:")
                    print(f"Source: {result['source']}")
                    print(f"Content: {result['content']}")
                responses.append(response)
            else:
                response = rag.query(question)
                responses.append(response)
                print(f"\nQuestion: {question}")
                print(f"Answer: {response['result']}")

    return responses

# if __name__ == "__main__":
#     main()

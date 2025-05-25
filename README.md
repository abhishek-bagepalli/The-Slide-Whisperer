# SlideWhisperer

An AI-powered presentation generation system that transforms documents into beautiful, professional slides. SlideWhisperer uses advanced AI to understand your content, generate appropriate layouts, and create engaging presentations with minimal effort. This was created by Abhishek Bagepalli (abagepal@purdue.edu), and Abhishek Baskar (baskar2@purdue.edu).

## Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with the following content:
```
OPENAI_API_KEY=your_openai_api_key
LLAMA_CLOUD_API_KEY=your_llama_parse_api_key
```

## Usage

1. Place your PDF and Word documents in a directory (e.g., `./documents/`)

2. Modify the `document_paths` list in `main()` function of `multi_document_rag.py` to include your document paths:
```python
document_paths = [
    "./documents/doc1.pdf",
    "./documents/doc2.docx"
]
```

3. Run the script:
```bash
python multi_document_rag.py
```

## Features

- Intelligent document processing (PDF, DOCX)
- Smart content extraction and organization
- AI-powered slide layout generation
- Automatic image generation and placement
- Professional presentation styling
- Multi-document RAG (Retrieval Augmented Generation) for enhanced content understanding

## Directory Structure

```
.
├── multi_document_rag.py    # Main RAG implementation
├── document_parser.py       # Document parsing utilities
├── requirements.txt         # Project dependencies
├── .env                    # Environment variables
├── chroma_db/             # Vector database storage
└── documents/             # Directory for input documents
```

## Example Usage

```python
from multi_document_rag import MultiDocumentRAG

# Initialize the RAG system
rag = MultiDocumentRAG()

# Process documents
document_paths = ["./documents/doc1.pdf", "./documents/doc2.docx"]
rag.process_documents(document_paths)

# Query the system
question = "What are the main topics discussed in these documents?"
response = rag.query(question)
print(response["result"])
``` 

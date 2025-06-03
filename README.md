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

## Deployment

### Backend Deployment

1. Set up a Python environment on your server:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
# Create .env file with your API keys
OPENAI_API_KEY=your_openai_api_key
LLAMA_CLOUD_API_KEY=your_llama_parse_api_key
```

3. Start the FastAPI server:
```bash
cd backend
uvicorn api:app --host 0.0.0.0 --port 8000
```

### Frontend Deployment

1. Install Node.js dependencies:
```bash
cd frontend
npm install
```

2. Build the Next.js application:
```bash
npm run build
```

3. Start the production server:
```bash
npm start
```

### Production Deployment Options

1. **Backend Deployment Options:**
   - Deploy on a cloud platform (AWS, Google Cloud, Azure)
   - Use a container service (Docker + Kubernetes)
   - Deploy on a VPS (DigitalOcean, Linode)

2. **Frontend Deployment Options:**
   - Deploy on Vercel (recommended for Next.js)
   - Deploy on Netlify
   - Deploy on AWS Amplify

3. **Environment Setup:**
   - Set up a reverse proxy (Nginx/Apache)
   - Configure SSL certificates
   - Set up proper CORS settings
   - Configure environment variables on the deployment platform

## Azure Deployment

### Prerequisites
1. Azure Account
2. Azure CLI installed
3. GitHub account (for CI/CD)

### Backend Deployment (Azure App Service)

1. Create Azure resources:
```bash
# Login to Azure
az login

# Create a resource group
az group create --name slide-whisperer-rg --location eastus

# Create an App Service plan
az appservice plan create --name slide-whisperer-plan --resource-group slide-whisperer-rg --sku B1 --is-linux

# Create the web app
az webapp create --name slide-whisperer-backend --resource-group slide-whisperer-rg --plan slide-whisperer-plan --runtime "PYTHON:3.11"

# Create Azure Blob Storage
az storage account create --name slidewhispererstorage --resource-group slide-whisperer-rg --location eastus --sku Standard_LRS
```

2. Configure environment variables in Azure Portal:
   - Go to Azure Portal > App Service > Configuration
   - Add the following application settings:
     - OPENAI_API_KEY
     - LLAMA_CLOUD_API_KEY
     - AZURE_STORAGE_CONNECTION_STRING

3. Deploy using GitHub Actions:
   - Fork this repository
   - Go to Azure Portal > App Service > Deployment Center
   - Choose GitHub Actions
   - Select your repository and branch
   - The deployment will start automatically

### Frontend Deployment (Azure Static Web Apps)

1. Create Static Web App:
```bash
# Create Static Web App
az staticwebapp create --name slide-whisperer-frontend --resource-group slide-whisperer-rg --location eastus --sku Free
```

2. Deploy using GitHub Actions:
   - Go to Azure Portal > Static Web App > Deployment
   - Connect your GitHub repository
   - Configure build settings:
     - Build command: `npm run build`
     - Output location: `.next`

### Microsoft Office Integration

To enable PowerPoint embedding and editing:

1. Register your application in Azure AD:
   - Go to Azure Portal > Azure Active Directory > App registrations
   - Create new registration
   - Add Microsoft Graph API permissions for Office files

2. Configure CORS in your backend:
   - Add the following to your FastAPI app:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://*.azurestaticapps.net"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

3. Add Microsoft Office Web Add-in support:
   - Create a manifest file for Office Add-in
   - Configure the add-in in your frontend application

### Monitoring and Maintenance

1. Set up Azure Monitor:
   - Configure Application Insights
   - Set up alerts for errors and performance issues

2. Regular maintenance:
   - Monitor storage usage
   - Review and rotate API keys
   - Update dependencies regularly

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

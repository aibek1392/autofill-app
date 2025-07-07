# AI Autofill Form App - Backend

## 🏗️ Architecture

The backend is built with:
- **FastAPI** - Modern Python web framework
- **LangChain** - LLM application framework
- **LangGraph** - Graph-based workflows
- **LangSmith** - LLM observability and monitoring
- **OpenAI API** - GPT-4 and embeddings
- **Pinecone** - Vector database for embeddings
- **Supabase** - PostgreSQL database and auth
- **Tesseract OCR** - Text extraction from images/PDFs

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file in the backend directory:

```bash
# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=autofill-form-app

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here
PINECONE_INDEX_NAME=autofill-documents

# Supabase
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# App Configuration
DEBUG=true
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB in bytes
```

### 3. Database Setup (Supabase)

Run the following SQL in your Supabase SQL editor:

```sql
-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Documents uploaded by users
CREATE TABLE uploaded_documents (
    doc_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    file_size INTEGER NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    processing_status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vector chunks from processed documents
CREATE TABLE vector_chunks (
    chunk_id VARCHAR(255) PRIMARY KEY,
    doc_id UUID REFERENCES uploaded_documents(doc_id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Filled forms history
CREATE TABLE filled_forms (
    form_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    original_form_name VARCHAR(255) NOT NULL,
    filled_form_url VARCHAR(500) NOT NULL,
    filled_fields JSONB DEFAULT '{}',
    missing_fields JSONB DEFAULT '[]',
    confidence_scores JSONB DEFAULT '{}',
    processing_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE uploaded_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE vector_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE filled_forms ENABLE ROW LEVEL SECURITY;

-- RLS Policies (add these for each table)
CREATE POLICY "Users can manage their own documents" ON uploaded_documents
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own chunks" ON vector_chunks
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own forms" ON filled_forms
    USING (auth.uid() = user_id);
```

### 4. Pinecone Setup

1. Create a Pinecone account and get API key
2. Create an index with:
   - Dimension: 1536 (for OpenAI ada-002 embeddings)
   - Metric: cosine
   - Name: `autofill-documents`

### 5. Install System Dependencies

For OCR functionality:

**macOS:**
```bash
brew install tesseract
brew install poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install poppler-utils
```

**Windows:**
- Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
- Download Poppler from: http://blog.alivate.com.au/poppler-windows/

### 6. Run the Server

```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📁 Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration and settings
├── requirements.txt       # Python dependencies
├── database/
│   ├── supabase_client.py  # Supabase database client
│   ├── pinecone_client.py  # Pinecone vector database client
│   └── schema.sql         # Database schema
├── services/
│   ├── document_processor.py  # OCR and document processing
│   ├── rag_service.py        # RAG pipeline with LangChain
│   └── form_filler.py        # PDF form filling service
└── uploads/               # File upload directory
```

## 🔄 Core Workflows

### Document Processing Pipeline
1. **Upload** → File validation and storage
2. **OCR** → Text extraction (PDF text extraction + Tesseract fallback)
3. **Chunking** → Split text into manageable chunks
4. **Embedding** → Generate OpenAI embeddings
5. **Storage** → Store vectors in Pinecone + metadata in Supabase

### Form Filling Pipeline
1. **Form Upload** → PDF form analysis
2. **Field Extraction** → AI identifies fillable fields
3. **Data Matching** → Vector search for relevant user data
4. **Field Population** → AI fills fields with found data
5. **PDF Generation** → Create filled PDF with overlay

### RAG Query Pipeline
1. **Query** → User question or form field request
2. **Embedding** → Generate query embedding
3. **Search** → Vector similarity search in Pinecone
4. **Context** → Retrieve relevant document chunks
5. **Generation** → LLM generates response with context

## 📊 API Endpoints

### Document Management
- `POST /api/upload` - Upload documents
- `GET /api/documents` - Get user documents
- `GET /api/download/{filename}` - Download files

### Form Processing
- `POST /api/upload-form` - Upload and fill form
- `GET /api/filled-forms` - Get filled forms history
- `POST /api/missing-field-suggestions` - Get AI suggestions

### Chat/Query
- `POST /api/chat` - Chat with documents
- `GET /api/stats` - User statistics

### Health/Monitoring
- `GET /api/health` - Health check
- `GET /` - Basic status

## 🔧 Configuration

Key settings in `config.py`:
- **Chunk size**: 1000 characters with 200 overlap
- **Top-K search**: 5 most relevant documents
- **Similarity threshold**: 0.7
- **Max file size**: 10MB
- **Supported formats**: PDF, JPG, JPEG, PNG

## 🔍 Observability

### LangSmith Integration
- All LLM calls are traced
- Query performance metrics
- Context retrieval analysis
- Form filling accuracy tracking

### Structured Logging
- JSON formatted logs
- Request/response tracking
- Error monitoring
- Performance metrics

## 🚦 Testing

```bash
# Start the server
python main.py

# Test health endpoint
curl http://localhost:8000/api/health

# Test file upload (with authentication)
curl -X POST "http://localhost:8000/api/upload" \
  -H "Authorization: Bearer your_token" \
  -F "files=@test_document.pdf"
```

## 🔐 Security

- JWT-based authentication (integration with Supabase Auth)
- Row Level Security (RLS) in database
- File type validation
- File size limits
- CORS configuration
- Input sanitization

## 🐛 Troubleshooting

### Common Issues

1. **Tesseract not found**
   - Ensure Tesseract is installed and in PATH
   - Check with: `tesseract --version`

2. **Pinecone connection error**
   - Verify API key and environment
   - Check index exists with correct dimensions

3. **Supabase connection error**
   - Verify URL and service role key
   - Check database policies

4. **OpenAI API errors**
   - Verify API key
   - Check rate limits and billing

### Debug Mode

Set `DEBUG=true` in `.env` for detailed logging and auto-reload.

## 📈 Performance Tips

1. **Batch processing**: Upload multiple files together
2. **Async operations**: Background document processing
3. **Caching**: Consider Redis for frequent queries
4. **Index optimization**: Tune Pinecone index settings
5. **Chunking strategy**: Adjust chunk size based on content type

## 🔄 Updates

To update dependencies:
```bash
pip install -r requirements.txt --upgrade
```

To check for security vulnerabilities:
```bash
pip audit
``` 
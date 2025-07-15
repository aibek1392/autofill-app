# 🤖 DocuChat - AI Document Chat Assistant

**DocuChat** is an AI-powered document chat assistant that allows you to upload documents and have intelligent conversations about their content. Perfect for quickly extracting information from PDFs, invoices, bank statements, and other documents.


## ✨ Features

- 📄 **Document Upload**: Support for PDF and image files
- 💬 **AI Chat**: Ask questions about your documents and get instant answers
- 🚀 **Streaming Responses**: Real-time AI responses for better user experience
- 🔍 **Smart Search**: Vector-based document search with relevance scoring
- 🏦 **Financial Focus**: Optimized for bank statements, invoices, and financial documents
- 📊 **Document Management**: Track and organize your uploaded documents

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **OpenAI GPT-4** - AI chat and document analysis
- **Pinecone** - Vector database for document search
- **Supabase** - Database and authentication
- **LangChain** - AI framework for document processing

### Frontend
- **React** - Modern UI framework
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful icons

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API key
- Pinecone account
- Supabase account

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env
python main.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## 📱 Usage

1. **Upload Documents**: Drag and drop PDFs or images
2. **Wait for Processing**: Documents are automatically processed and indexed
3. **Start Chatting**: Ask questions about your documents
4. **Get Instant Answers**: AI provides relevant information with source citations

## 🔧 Configuration

Key environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `PINECONE_API_KEY` - Your Pinecone API key
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Your Supabase anonymous key

## 🚀 Deployment

Deploy for free using:
- **Backend**: Render
- **Frontend**: Vercel

See `DEPLOYMENT_GUIDE.md` for detailed instructions.

## 💡 Example Questions

- "What transactions are in my bank statement?"
- "What's the total amount of expenses this month?"
- "Who is the sender of this invoice?"
- "What's the due date for this payment?"
- "Summarize the key points from this document"

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**DocuChat** - Making document analysis as easy as having a conversation!ASk the chat any information you need from document 🚀 

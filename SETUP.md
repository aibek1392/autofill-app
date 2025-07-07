# AI Autofill Form App - Setup Guide

## 🔐 Security First - Environment Variables

This project uses environment variables to keep sensitive data secure. **Never commit your actual API keys to Git!**

### Required Environment Variables

Create a `.env` file in the `backend/` directory with the following variables:

```bash
# OpenAI Configuration (Required)
OPENAI_API_KEY=your_actual_openai_api_key

# Pinecone Configuration (Required for vector search)
PINECONE_API_KEY=your_actual_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=autofill-documents

# Supabase Configuration (Required for database and auth)
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# App Configuration
DEBUG=true
CORS_ORIGINS=http://localhost:3000
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760
```

### Optional Environment Variables

```bash
# LangSmith Configuration (for AI observability)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=autofill-form-app

# Model Configuration
EMBEDDING_MODEL=text-embedding-ada-002
CHAT_MODEL=gpt-3.5-turbo
TEMPERATURE=0.1
MAX_TOKENS=2000
```

## 🚀 Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API keys
cp .env.example .env
# Edit .env with your actual API keys

# Start the backend server
python main.py
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

### 3. Chrome Extension Setup

```bash
cd chrome-extension

# Load the extension in Chrome:
# 1. Open Chrome and go to chrome://extensions/
# 2. Enable "Developer mode"
# 3. Click "Load unpacked" and select the chrome-extension folder
```

## 🔧 Services Setup

### OpenAI
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create an account and get your API key
3. Add it to your `.env` file

### Pinecone
1. Go to [Pinecone Console](https://app.pinecone.io/)
2. Create an account and get your API key
3. Create an index named `autofill-documents` with 1536 dimensions
4. Add your API key and environment to `.env`

### Supabase
1. Go to [Supabase](https://supabase.com/)
2. Create a new project
3. Run the SQL schema from `backend/database/schema.sql`
4. Get your project URL and keys from Settings > API
5. Add them to your `.env` file

## 📁 Project Structure

```
AUTOFILLFORM_APP/
├── backend/                 # FastAPI backend
│   ├── .env                # Environment variables (not in Git)
│   ├── .env.example        # Example environment file
│   ├── main.py             # FastAPI application
│   ├── config.py           # Configuration settings
│   ├── services/           # AI and processing services
│   ├── database/           # Database clients and schema
│   └── uploads/            # User uploaded files (not in Git)
├── frontend/               # React frontend
│   ├── src/                # React components
│   ├── public/             # Static files
│   └── package.json        # Dependencies
├── chrome-extension/       # Chrome extension
│   ├── manifest.json       # Extension manifest
│   ├── content.js          # Content script
│   └── background.js       # Background script
└── .gitignore             # Git ignore rules
```

## 🛡️ Security Checklist

Before pushing to GitHub, ensure:

- [ ] `.env` file is in `.gitignore`
- [ ] No API keys are hardcoded in source code
- [ ] `uploads/` directory is in `.gitignore`
- [ ] `venv/` directory is in `.gitignore`
- [ ] `node_modules/` directory is in `.gitignore`
- [ ] Log files are in `.gitignore`
- [ ] Test and debug files are in `.gitignore`

## 🔍 Verifying Security

Run these commands to check for sensitive data:

```bash
# Check for API keys in code
grep -r "sk-" .
grep -r "pk_" .
grep -r "AIza" .

# Check for .env files
find . -name ".env*" -type f

# Check what will be committed
git status
git diff --cached
```

## 🚨 Common Security Mistakes

1. **Never commit `.env` files** - They contain your actual API keys
2. **Don't hardcode secrets** - Always use environment variables
3. **Check your commits** - Review what you're about to push
4. **Use .env.example** - Show others what variables are needed
5. **Rotate keys regularly** - Change API keys periodically

## 🆘 Troubleshooting

### Backend Issues
- Check that all environment variables are set
- Verify API keys are valid
- Check Pinecone index exists and has correct dimensions
- Ensure Supabase tables are created

### Frontend Issues
- Check that backend is running on port 8000
- Verify CORS settings in backend
- Check browser console for errors

### Chrome Extension Issues
- Reload the extension after making changes
- Check browser console for errors
- Verify manifest.json is valid

## 📞 Support

If you encounter issues:
1. Check the logs in the backend console
2. Verify all environment variables are set correctly
3. Ensure all services (OpenAI, Pinecone, Supabase) are accessible
4. Check the browser console for frontend errors 
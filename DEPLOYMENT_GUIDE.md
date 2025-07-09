# 🚀 Deployment Guide: DocuChat - Render + Vercel

This guide will help you deploy your **DocuChat** app to **Render** (backend) and **Vercel** (frontend) for **free**.

## 📋 Prerequisites

Before starting, make sure you have:

- ✅ **GitHub account** with your code pushed
- ✅ **OpenAI API key** (required)
- ✅ **Pinecone account** and API key (required)
- ✅ **Supabase account** and keys (required)
- ✅ **Render account** (free signup)
- ✅ **Vercel account** (free signup)

---

## 🔧 Step 1: Deploy Backend to Render

### 1.1 Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account
3. Connect your GitHub repository

### 1.2 Create Web Service
1. Click **"New"** → **"Web Service"**
2. Connect your GitHub repository
3. Select your repository
4. Configure the service:
   - **Name:** `docuchat-backend` (or your preferred name)
   - **Root Directory:** `backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free

### 1.3 Set Environment Variables
In the Render dashboard, go to **Environment** and add these variables:

```bash
# Required - OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Required - Pinecone
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here
PINECONE_INDEX_NAME=autofill-documents

# Required - Supabase
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# Optional - LangSmith (for monitoring)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langchain_api_key_here
LANGCHAIN_PROJECT=autofill-form-app

# App Configuration
DEBUG=false
CORS_ORIGINS=https://your-frontend-url.vercel.app,http://localhost:3000
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760
```

### 1.4 Deploy
1. Click **"Create Web Service"**
2. Wait for the build to complete (5-10 minutes)
3. Note your backend URL: `https://your-app-name.onrender.com`

---

## 🎨 Step 2: Deploy Frontend to Vercel

### 2.1 Create Vercel Account
1. Go to [vercel.com](https://vercel.com)
2. Sign up with your GitHub account

### 2.2 Import Project
1. Click **"New Project"**
2. Import your GitHub repository
3. Configure the project:
   - **Framework Preset:** React
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `build`
   - **Install Command:** `npm install`

### 2.3 Set Environment Variables
In the Vercel dashboard, go to **Settings** → **Environment Variables**:

```bash
# Required - Backend URL (replace with your Render URL)
REACT_APP_API_URL=https://your-backend-name.onrender.com

# Optional - Supabase (if using authentication)
REACT_APP_SUPABASE_URL=your_supabase_url_here
REACT_APP_SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

### 2.4 Deploy
1. Click **"Deploy"**
2. Wait for the build to complete (2-5 minutes)
3. Note your frontend URL: `https://your-app-name.vercel.app`

---

## 🔄 Step 3: Update CORS Settings

### 3.1 Update Backend CORS
1. Go back to your **Render** dashboard
2. Update the `CORS_ORIGINS` environment variable:
   ```bash
   CORS_ORIGINS=https://your-frontend-url.vercel.app,http://localhost:3000
   ```
3. **Redeploy** the backend service

---

## 🧪 Step 4: Test Your Deployment

### 4.1 Test Backend
Visit your backend URL: `https://your-backend-name.onrender.com`
- You should see: `{"message": "DocuChat API is running!"}`

### 4.2 Test Frontend
Visit your frontend URL: `https://your-app-name.vercel.app`
- The app should load correctly
- Try uploading a document
- Test the chat functionality

---

## 🚨 Common Issues & Solutions

### Backend Issues

**Issue:** Build fails with "No module named 'xyz'"
**Solution:** Make sure all dependencies are in `requirements.txt`

**Issue:** App crashes on startup
**Solution:** Check environment variables are set correctly

**Issue:** CORS errors
**Solution:** Update `CORS_ORIGINS` with your Vercel URL

### Frontend Issues

**Issue:** API calls fail
**Solution:** Check `REACT_APP_API_URL` points to your Render URL

**Issue:** Build fails
**Solution:** Make sure all dependencies are in `package.json`

---

## 📊 Monitoring & Logs

### Render Logs
- Go to your service dashboard
- Click **"Logs"** to see real-time logs
- Monitor for errors and performance

### Vercel Logs
- Go to your project dashboard
- Click **"Functions"** → **"View Function Logs"**
- Monitor build and runtime logs

---

## 🔄 Updating Your App

### For Backend Changes:
1. Push changes to GitHub
2. Render will auto-deploy (if auto-deploy is enabled)
3. Or manually redeploy from Render dashboard

### For Frontend Changes:
1. Push changes to GitHub
2. Vercel will auto-deploy
3. Or manually redeploy from Vercel dashboard

---

## 💡 Performance Tips

### Backend Optimization:
- **Free tier sleeps** after 15 minutes of inactivity
- **Cold start** takes ~30 seconds to wake up
- Consider upgrading to paid plan for production

### Frontend Optimization:
- **Vercel is fast** and has global CDN
- **Automatic optimizations** for React apps
- **Preview deployments** for every commit

---

## 🎯 Your Deployed URLs

After deployment, you'll have:

- **Backend API:** `https://your-backend-name.onrender.com`
- **Frontend App:** `https://your-app-name.vercel.app`

Share the frontend URL with your instructor! 🎉

---

## 🆘 Need Help?

If you encounter issues:
1. Check the logs in Render/Vercel dashboards
2. Verify all environment variables are set
3. Test API endpoints individually
4. Check GitHub repository is up to date

**Total Cost: $0** ✅ **Perfect for demos and presentations!** 
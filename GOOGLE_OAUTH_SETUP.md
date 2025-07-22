# 🔐 Google OAuth Setup Guide for AutoFill Form App

This guide will help you enable Google Sign-In for your AutoFill Form App.

## 🚨 Current Issue
You're getting the error: `{"code":400,"error_code":"validation_failed","msg":"Unsupported provider: provider is not enabled"}`

This means Google OAuth is not enabled in your Supabase project.

---

## 📋 Step-by-Step Setup

### Step 1: Enable Google OAuth in Supabase

1. **Go to Supabase Dashboard**: https://app.supabase.com
2. **Select your project**
3. **Navigate to**: `Authentication` → `Providers`
4. **Find "Google" in the list**
5. **Toggle the switch to enable Google OAuth**

### Step 2: Create Google OAuth Credentials

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create a new project or select existing one**
3. **Enable APIs**:
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API" and enable it
   - Search for "Google Identity" and enable it

4. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - If prompted, configure OAuth consent screen first

5. **Configure OAuth Consent Screen** (if needed):
   - **User Type**: External
   - **App name**: AutoFill Form App
   - **User support email**: Your email
   - **Developer contact information**: Your email
   - **Authorized domains**: Add your domains

6. **Create OAuth 2.0 Client ID**:
   - **Application type**: Web application
   - **Name**: AutoFill Form App
   - **Authorized JavaScript origins**:
     ```
     http://localhost:3000
     https://your-frontend-domain.vercel.app
     ```
   - **Authorized redirect URIs**:
     ```
     https://your-project-id.supabase.co/auth/v1/callback
     ```

### Step 3: Add Credentials to Supabase

1. **Back in Supabase Dashboard** → `Authentication` → `Providers` → `Google`
2. **Enter your credentials**:
   - **Client ID**: Your Google OAuth Client ID
   - **Client Secret**: Your Google OAuth Client Secret
3. **Click "Save"**

### Step 4: Test the Setup

1. **Restart your development server** (if running locally)
2. **Try signing in with Google**
3. **Check browser console for any errors**

---

## 🔧 Troubleshooting

### Common Issues

**Issue**: "Unsupported provider: provider is not enabled"
**Solution**: Make sure Google OAuth is enabled in Supabase Dashboard

**Issue**: "redirect_uri_mismatch"
**Solution**: Check that your redirect URI in Google Console matches exactly:
```
https://your-project-id.supabase.co/auth/v1/callback
```

**Issue**: "invalid_client"
**Solution**: Verify your Client ID and Client Secret are correct

**Issue**: "access_denied"
**Solution**: Check your OAuth consent screen configuration

### Debug Steps

1. **Check Supabase Configuration**:
   ```bash
   # In browser console
   console.log('Supabase URL:', process.env.REACT_APP_SUPABASE_URL)
   console.log('Supabase Key:', process.env.REACT_APP_SUPABASE_ANON_KEY ? 'SET' : 'NOT SET')
   ```

2. **Check Google OAuth Status**:
   - Go to Supabase Dashboard → Authentication → Providers
   - Verify Google is enabled (toggle is ON)
   - Verify Client ID and Secret are filled

3. **Check Network Tab**:
   - Open browser DevTools → Network tab
   - Try Google sign-in
   - Look for any failed requests

---

## 📝 Environment Variables

Make sure your frontend `.env` file has:

```bash
REACT_APP_SUPABASE_URL=https://your-project-id.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-supabase-anon-key
REACT_APP_API_URL=https://autofill-backend-a64u.onrender.com
```

---

## 🎯 Expected Flow

1. User clicks "Continue with Google"
2. Browser redirects to Google OAuth page
3. User authorizes the app
4. Google redirects back to Supabase callback URL
5. Supabase creates/updates user account
6. User is redirected to `/dashboard`

---

## 🚀 Production Deployment

For production, make sure to:

1. **Update Google OAuth redirect URIs** to include your production domain
2. **Update Supabase CORS settings** to allow your production domain
3. **Test the flow in production environment**

---

## 📞 Need Help?

If you're still having issues:

1. Check the browser console for detailed error messages
2. Verify all environment variables are set correctly
3. Ensure your Supabase project is active and not paused
4. Check that your Google Cloud project has billing enabled (if required)

The most common issue is simply forgetting to enable Google OAuth in the Supabase Dashboard! 
# Keep-Alive Service Setup Guide

This guide helps you set up a keep-alive service to reduce cold starts on your Render backend.

## 🎯 What This Does

- **Pings your backend every 5-10 minutes** to keep it "warm"
- **Reduces cold start delays** when users make requests
- **Improves user experience** with faster response times
- **Monitors backend health** and logs any issues

## 🚀 Setup Options

### Option 1: Vercel Edge Function (Recommended)

1. **Deploy the Edge Function**:
   - The `frontend/api/keep-alive.js` file is already created
   - Deploy your frontend to Vercel (if not already done)
   - The function will be available at: `https://your-app.vercel.app/api/keep-alive`

2. **Set up Cron Job**:
   - Go to [cron-job.org](https://cron-job.org)
   - Create a free account
   - Add a new cron job with these settings:
     - **URL**: `https://your-app.vercel.app/api/keep-alive`
     - **Schedule**: Every 5 minutes (`*/5 * * * *`)
     - **Method**: GET
     - **Timeout**: 30 seconds

### Option 2: UptimeRobot (Alternative)

1. **Create Account**: [uptimerobot.com](https://uptimerobot.com)
2. **Add Monitor**:
   - **Monitor Type**: HTTP(s)
   - **URL**: `https://autofill-backend-a64u.onrender.com/api/ping`
   - **Check Interval**: 5 minutes
   - **Alert**: Email notifications if backend goes down

### Option 3: GitHub Actions (Free)

Create `.github/workflows/keep-alive.yml`:

```yaml
name: Keep Alive

on:
  schedule:
    - cron: '*/5 * * * *'  # Every 5 minutes
  workflow_dispatch:  # Manual trigger

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Backend
        run: |
          curl -X GET "https://autofill-backend-a64u.onrender.com/api/ping" \
            -H "User-Agent: GitHub-Actions-KeepAlive/1.0" \
            -H "Accept: application/json" \
            --max-time 30
```

## 🔧 Testing

### Test Locally

```bash
cd backend
python test_ping.py
```

### Test Production

```bash
curl -X GET "https://autofill-backend-a64u.onrender.com/api/ping" \
  -H "Accept: application/json"
```

Expected response:
```json
{
  "status": "pong",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "message": "Server is alive"
}
```

## 📊 Monitoring

### Check Keep-Alive Logs

1. **Vercel Dashboard**: View function logs at your Vercel dashboard
2. **Render Logs**: Check backend logs for ping requests
3. **Cron-job.org**: View execution history and success rates

### Health Check Endpoint

Use the detailed health check for monitoring:

```bash
curl "https://autofill-backend-a64u.onrender.com/api/health"
```

This returns:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "services": {
    "api": "running",
    "pinecone": "connected",
    "supabase": "connected"
  }
}
```

## ⚙️ Configuration

### Backend Endpoints

- **Ping**: `/api/ping` - Simple keep-alive (fast)
- **Health**: `/api/health` - Detailed health check (slower)

### Timing Recommendations

- **Keep-Alive**: Every 5-10 minutes
- **Health Check**: Every 30 minutes (for monitoring)
- **Timeout**: 10-30 seconds

## 🚨 Troubleshooting

### Common Issues

1. **Backend Not Responding**:
   - Check Render logs for errors
   - Verify the backend URL is correct
   - Check if Pinecone/Supabase are causing timeouts

2. **Cron Job Failing**:
   - Verify the URL is accessible
   - Check if the function returns proper JSON
   - Increase timeout if needed

3. **Too Many Requests**:
   - Increase interval to 10-15 minutes
   - Monitor Render usage limits
   - Consider using Render's built-in health checks

### Logs to Check

- **Vercel Function Logs**: For keep-alive service issues
- **Render Logs**: For backend ping requests
- **Cron Service Logs**: For scheduling issues

## 💡 Tips

1. **Start with 5-minute intervals** and adjust based on usage
2. **Monitor your Render usage** to avoid hitting limits
3. **Set up alerts** for when the backend goes down
4. **Use the health check** for more detailed monitoring
5. **Consider timezone differences** when setting up cron jobs

## 🔄 Next Steps

1. Deploy the keep-alive function to Vercel
2. Set up the cron job at cron-job.org
3. Test the setup with the provided test script
4. Monitor logs for the first few days
5. Adjust timing based on your usage patterns

This setup should significantly reduce cold starts and improve your app's responsiveness! 🚀 
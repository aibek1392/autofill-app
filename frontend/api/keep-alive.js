// Vercel Edge Function for keep-alive service
// This function will be called by a cron job to ping your backend

export default async function handler(req, res) {
  // Only allow GET requests
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const backendUrl = 'https://autofill-backend-a64u.onrender.com';
  
  try {
    console.log(`🔄 Pinging backend at ${new Date().toISOString()}`);
    
    // Ping the simple ping endpoint
    const pingResponse = await fetch(`${backendUrl}/api/ping`, {
      method: 'GET',
      headers: {
        'User-Agent': 'Autofill-App-KeepAlive/1.0',
        'Accept': 'application/json',
      },
      // Add a reasonable timeout
      signal: AbortSignal.timeout(10000), // 10 seconds
    });

    if (pingResponse.ok) {
      const pingData = await pingResponse.json();
      console.log('✅ Backend ping successful:', pingData);
      
      return res.status(200).json({
        success: true,
        timestamp: new Date().toISOString(),
        backend_status: 'alive',
        ping_response: pingData
      });
    } else {
      console.log('⚠️ Backend ping failed with status:', pingResponse.status);
      
      return res.status(200).json({
        success: false,
        timestamp: new Date().toISOString(),
        backend_status: 'error',
        error: `HTTP ${pingResponse.status}`,
        message: 'Backend responded but with error status'
      });
    }
    
  } catch (error) {
    console.error('❌ Backend ping failed:', error.message);
    
    return res.status(200).json({
      success: false,
      timestamp: new Date().toISOString(),
      backend_status: 'down',
      error: error.message,
      message: 'Backend is not responding'
    });
  }
}

// Optional: Add a health check endpoint for the keep-alive service itself
export async function healthCheck(req, res) {
  return res.status(200).json({
    status: 'healthy',
    service: 'keep-alive',
    timestamp: new Date().toISOString(),
    message: 'Keep-alive service is running'
  });
} 
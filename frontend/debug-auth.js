// Debug script to check authentication status
// Run this in your browser console on the frontend

console.log('=== Authentication Debug ===');

// Check if Supabase is available
if (typeof window !== 'undefined' && window.supabase) {
  console.log('✅ Supabase client is available');
  
  // Get current user
  window.supabase.auth.getUser().then(({ data: { user }, error }) => {
    if (error) {
      console.error('❌ Error getting user:', error);
    } else if (user) {
      console.log('✅ User is logged in:');
      console.log('  - User ID:', user.id);
      console.log('  - Email:', user.email);
      console.log('  - Created:', user.created_at);
    } else {
      console.log('❌ No user logged in');
    }
  });
  
  // Get current session
  window.supabase.auth.getSession().then(({ data: { session }, error }) => {
    if (error) {
      console.error('❌ Error getting session:', error);
    } else if (session) {
      console.log('✅ Session is active:');
      console.log('  - Access token exists:', !!session.access_token);
      console.log('  - Expires at:', new Date(session.expires_at * 1000));
    } else {
      console.log('❌ No active session');
    }
  });
} else {
  console.log('❌ Supabase client not available');
}

// Check environment variables
console.log('\n=== Environment Variables ===');
console.log('REACT_APP_SUPABASE_URL:', process.env.REACT_APP_SUPABASE_URL ? '✅ Set' : '❌ Not set');
console.log('REACT_APP_SUPABASE_ANON_KEY:', process.env.REACT_APP_SUPABASE_ANON_KEY ? '✅ Set' : '❌ Not set');
console.log('REACT_APP_API_URL:', process.env.REACT_APP_API_URL || 'Using default'); 
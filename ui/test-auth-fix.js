/**
 * Test script to verify authentication token handling
 * Run this in the browser console after logging in
 */

async function testAuthTokenHandling() {
  console.log('🔍 Testing Authentication Token Handling...');
  
  // Test 1: Check localStorage tokens
  console.log('\n1. Checking localStorage tokens:');
  const localToken = localStorage.getItem('token');
  const supabaseToken = localStorage.getItem('supabase.auth.token');
  console.log('localStorage token:', localToken ? '✅ Found' : '❌ Missing');
  console.log('supabase.auth.token:', supabaseToken ? '✅ Found' : '❌ Missing');
  
  // Test 2: Check Supabase session
  console.log('\n2. Checking Supabase session:');
  try {
    const { createClient } = await import('@supabase/supabase-js');
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    
    if (supabaseUrl && supabaseAnonKey) {
      const supabase = createClient(supabaseUrl, supabaseAnonKey);
      const { data: { session }, error } = await supabase.auth.getSession();
      
      if (error) {
        console.log('❌ Supabase session error:', error.message);
      } else if (session) {
        console.log('✅ Supabase session found');
        console.log('User:', session.user?.email);
        console.log('Access token:', session.access_token ? '✅ Present' : '❌ Missing');
        console.log('Token expires at:', new Date(session.expires_at * 1000).toLocaleString());
      } else {
        console.log('❌ No Supabase session');
      }
    } else {
      console.log('❌ Supabase environment variables missing');
    }
  } catch (error) {
    console.log('❌ Error checking Supabase session:', error.message);
  }
  
  // Test 3: Test API call with token
  console.log('\n3. Testing API call:');
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || '***REMOVED***';
  const testUrl = `${apiBaseUrl}/health`;
  
  try {
    const response = await fetch(testUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localToken || 'no-token'}`,
        'Content-Type': 'application/json',
      },
    });
    
    console.log('API Response Status:', response.status);
    console.log('API Response OK:', response.ok ? '✅' : '❌');
    
    if (response.ok) {
      const data = await response.json();
      console.log('API Response Data:', data);
    } else {
      const errorText = await response.text();
      console.log('API Error:', errorText);
    }
  } catch (error) {
    console.log('❌ API call failed:', error.message);
  }
  
  console.log('\n✅ Authentication test completed');
}

// Run the test
testAuthTokenHandling();

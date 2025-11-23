/**
 * Secure Supabase Client Configuration
 * Follows environment-based credential management pattern
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';

/**
 * Get Supabase client with credentials from environment
 * Never hardcodes credentials - always reads from process.env
 * 
 * @throws {Error} If SUPABASE_URL or SUPABASE_KEY are not set
 * @returns {SupabaseClient} Configured Supabase client
 */
export function getSupabaseClient(): SupabaseClient {
  const supabaseUrl = process.env.SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_KEY;
  
  if (!supabaseUrl || !supabaseKey) {
    throw new Error(
      'Supabase credentials not configured.\n\n' +
      'Required environment variables:\n' +
      '  - SUPABASE_URL: Your Supabase project URL\n' +
      '  - SUPABASE_KEY: Your Supabase anon/public key\n\n' +
      'Get your credentials from:\n' +
      '  https://supabase.com/dashboard/project/_/settings/api\n\n' +
      'Set them using:\n' +
      '  export SUPABASE_URL="https://xxx.supabase.co"\n' +
      '  export SUPABASE_KEY="your-key-here"\n' +
      'Or create a .env file (not committed to git)'
    );
  }
  
  return createClient(supabaseUrl, supabaseKey);
}

/**
 * Validate Supabase connection
 * Tests connectivity without exposing credentials
 */
export async function validateConnection(): Promise<boolean> {
  try {
    const client = getSupabaseClient();
    const { error } = await client.from('file_imports').select('count').limit(1);
    
    if (error) {
      console.error('Supabase connection test failed:', error.message);
      return false;
    }
    
    return true;
  } catch (err) {
    console.error('Failed to connect to Supabase:', err instanceof Error ? err.message : String(err));
    return false;
  }
}

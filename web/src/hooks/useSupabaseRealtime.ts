/**
 * MAPS - Supabase Realtime Hook
 * 
 * Custom React hook for subscribing to Supabase realtime database changes
 */

import { useEffect, useState, useCallback } from 'react';
import { createClient, RealtimeChannel, SupabaseClient } from '@supabase/supabase-js';

interface UseSupabaseRealtimeOptions {
  table: string;
  event?: 'INSERT' | 'UPDATE' | 'DELETE' | '*';
  filter?: string;
  enabled?: boolean;
}

interface RealtimePayload<T = any> {
  eventType: 'INSERT' | 'UPDATE' | 'DELETE';
  new: T | null;
  old: T | null;
  errors: any[];
}

interface UseSupabaseRealtimeReturn<T = any> {
  data: RealtimePayload<T> | null;
  isConnected: boolean;
  error: Error | null;
  subscribe: () => void;
  unsubscribe: () => void;
}

let supabaseClient: SupabaseClient | null = null;

function getSupabaseClient(): SupabaseClient | null {
  if (supabaseClient) return supabaseClient;

  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
  const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseKey) {
    console.warn('Supabase credentials not configured');
    return null;
  }

  supabaseClient = createClient(supabaseUrl, supabaseKey);
  return supabaseClient;
}

export function useSupabaseRealtime<T = any>({
  table,
  event = '*',
  filter,
  enabled = true,
}: UseSupabaseRealtimeOptions): UseSupabaseRealtimeReturn<T> {
  const [data, setData] = useState<RealtimePayload<T> | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [channel, setChannel] = useState<RealtimeChannel | null>(null);

  const unsubscribe = useCallback(() => {
    if (channel) {
      channel.unsubscribe();
      setChannel(null);
      setIsConnected(false);
    }
  }, [channel]);

  const subscribe = useCallback(() => {
    if (!enabled) return;

    const client = getSupabaseClient();
    if (!client) {
      setError(new Error('Supabase client not initialized'));
      return;
    }

    unsubscribe();

    try {
      let subscription = client
        .channel(`${table}_changes`)
        .on(
          'postgres_changes',
          {
            event: event,
            schema: 'public',
            table: table,
            filter: filter,
          },
          (payload: any) => {
            setData({
              eventType: payload.eventType,
              new: payload.new,
              old: payload.old,
              errors: payload.errors || [],
            });
          }
        );

      subscription.subscribe((status: string) => {
        if (status === 'SUBSCRIBED') {
          setIsConnected(true);
          setError(null);
        } else if (status === 'CHANNEL_ERROR') {
          setError(new Error('Failed to subscribe to channel'));
          setIsConnected(false);
        } else if (status === 'TIMED_OUT') {
          setError(new Error('Subscription timed out'));
          setIsConnected(false);
        }
      });

      setChannel(subscription);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Subscription failed');
      setError(error);
      setIsConnected(false);
    }
  }, [table, event, filter, enabled, unsubscribe]);

  useEffect(() => {
    if (enabled) {
      subscribe();
    }
    return () => {
      unsubscribe();
    };
  }, [enabled, subscribe, unsubscribe]);

  return {
    data,
    isConnected,
    error,
    subscribe,
    unsubscribe,
  };
}

// Convenience hooks for common tables
export function useDocumentsRealtime(enabled = true) {
  return useSupabaseRealtime({
    table: 'canonical_documents',
    event: '*',
    enabled,
  });
}

export function useJobsRealtime(enabled = true) {
  return useSupabaseRealtime({
    table: 'batch_jobs',
    event: '*',
    enabled,
  });
}

export function useKeywordsRealtime(enabled = true) {
  return useSupabaseRealtime({
    table: 'keywords',
    event: '*',
    enabled,
  });
}

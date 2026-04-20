-- Run this migration once in Supabase SQL editor.
-- It allows persisting conversation messages even when no ticket is created yet.

alter table if exists public.messages
  alter column ticket_id drop not null;

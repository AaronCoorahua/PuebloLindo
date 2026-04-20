-- Run this in Supabase SQL editor when using STORAGE_BACKEND=supabase.

create table if not exists public.tickets (
  id uuid primary key,
  user_phone text not null,
  status text not null check (status in ('open', 'closed')),
  created_at timestamptz not null,
  updated_at timestamptz not null
);

create table if not exists public.messages (
  id uuid primary key,
  ticket_id uuid not null references public.tickets(id) on delete cascade,
  external_message_id text unique,
  sender text not null check (sender in ('user', 'system')),
  content text not null,
  created_at timestamptz not null
);

create index if not exists idx_tickets_phone_status
  on public.tickets(user_phone, status);

create index if not exists idx_messages_ticket_created
  on public.messages(ticket_id, created_at);

-- Recommended for production with PostgREST/Supabase API:
-- enable row level security;
-- create explicit policies for service role or secure server access.

-- Run this in Supabase SQL editor for tickets-only mode.

create table if not exists public.tickets (
  id uuid primary key,
  user_phone text not null,
  status text not null check (status in ('open', 'closed')),
  created_at timestamptz not null,
  updated_at timestamptz not null
);

create index if not exists idx_tickets_phone_status
  on public.tickets(user_phone, status);

-- Recommended for production with PostgREST/Supabase API:
-- enable row level security;
-- create explicit policies for service role or secure server access.

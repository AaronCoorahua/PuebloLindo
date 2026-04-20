-- Run this in Supabase SQL editor for ticket triage with conversation context.

create table if not exists public.tickets (
  id uuid primary key,
  user_phone text not null,
  status text not null check (status in ('open', 'closed')),
  area text not null default 'otros',
  title text not null default '',
  summary text not null default '',
  closed_by text null,
  closed_message text null,
  created_at timestamptz not null,
  updated_at timestamptz not null,
  last_activity_at timestamptz not null
);

alter table public.tickets add column if not exists area text not null default 'otros';
alter table public.tickets add column if not exists title text not null default '';
alter table public.tickets add column if not exists summary text not null default '';
alter table public.tickets add column if not exists closed_by text;
alter table public.tickets add column if not exists closed_message text;
alter table public.tickets add column if not exists last_activity_at timestamptz not null default now();

create index if not exists idx_tickets_phone_status
  on public.tickets(user_phone, status);

create index if not exists idx_tickets_phone_status_activity
  on public.tickets(user_phone, status, last_activity_at desc);

create table if not exists public.messages (
  id uuid primary key,
  ticket_id uuid references public.tickets(id) on delete cascade,
  user_phone text not null,
  external_message_id text null,
  sender text not null check (sender in ('user', 'agent')),
  content text not null,
  created_at timestamptz not null
);

alter table public.messages add column if not exists user_phone text;
alter table public.messages alter column ticket_id drop not null;

create index if not exists idx_messages_phone_created
  on public.messages(user_phone, created_at desc);

create unique index if not exists idx_messages_external_unique
  on public.messages(external_message_id)
  where external_message_id is not null;

-- Recommended for production with PostgREST/Supabase API:
-- enable row level security;
-- create explicit policies for service role or secure server access.

alter table if exists public.tickets
  add column if not exists closed_by text,
  add column if not exists closed_message text;
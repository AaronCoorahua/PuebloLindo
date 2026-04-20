alter table if exists public.tickets
  add column if not exists title text not null default '';
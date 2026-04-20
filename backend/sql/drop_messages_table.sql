-- Execute this once if you want to remove message persistence.
-- Safe order: drop index first (if exists), then table.

drop index if exists public.idx_messages_ticket_created;
drop table if exists public.messages;

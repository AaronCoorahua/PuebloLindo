update public.tickets
set title = left(
  trim(
    regexp_replace(
      split_part(coalesce(summary, ''), '|', 1),
      '^\s*Cliente\s+reporta:\s*',
      '',
      'i'
    )
  ),
  120
)
where coalesce(trim(title), '') = ''
  and coalesce(trim(summary), '') <> '';
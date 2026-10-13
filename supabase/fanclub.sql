-- The fan club of Hegel in Delhi (Supabase project hegel-in-delhi, eu-central-1).
-- The public can only join and count. Names are kept only for those who ask to be met, and enter the world only after the
-- site's owner sets `approved` in the table editor. The role ids are mirrored in world/data/visitors.json and docs/index.html.

create table if not exists public.fans (
  id bigint generated always as identity primary key,
  joined_at timestamptz not null default now(),
  meet boolean not null default false,
  name text,                       -- a first name or nickname, only when meet
  role text,                       -- a role id, only when meet
  approved boolean not null default false,
  met_on date,                     -- the day the world placed them; set by the world, not by the page
  constraint fans_meet_has_name check (not meet or (name is not null and role is not null)),
  constraint fans_name_shape check (name is null or char_length(name) between 1 and 24)
);
alter table public.fans enable row level security;
revoke all on table public.fans from anon, authenticated;

create or replace function public.join_fanclub(p_name text default null, p_role text default null, p_meet boolean default false)
returns bigint
language plpgsql
security definer
set search_path = public
as $$
declare
  roles constant text[] := array['parakeets', 'kites', 'ghalib', 'chai', 'auto', 'chess', 'dogs', 'scout', 'chhole', 'guide', 'schopenhauer', 'marxist', 'kantian', 'gita', 'goethe', 'phd', 'stamp', 'owl', 'forecast', 'diplomat'];
  recent int;
  total bigint;
begin
  p_meet := coalesce(p_meet, false);
  if p_meet then
    p_name := btrim(coalesce(p_name, ''));
    -- letters of any script, with the combining marks of Latin accents, the Indic scripts and Arabic/Urdu; space . ' ’ -
    if p_name = '' or char_length(p_name) > 24 or p_name !~ '^[[:alpha:]][[:alpha:]\u0300-\u036F\u0900-\u0DFF\u0600-\u06FF .''\u2019-]*$' then
      raise exception 'A first name or nickname, letters only, at most 24.' using errcode = '22023';
    end if;
    if p_role is null or not (p_role = any(roles)) then
      raise exception 'Choose one of the parts on the list.' using errcode = '22023';
    end if;
  end if;
  select count(*) into recent from public.fans where joined_at > now() - interval '1 hour';
  if recent >= 300 then
    raise exception 'The fan club is very busy just now. Try again in an hour.' using errcode = '53400';
  end if;
  insert into public.fans (meet, name, role) values (p_meet, case when p_meet then p_name end, case when p_meet then p_role end);
  select count(*) into total from public.fans;
  return total;
end;
$$;

create or replace function public.fan_count()
returns bigint
language sql
stable
security definer
set search_path = public
as $$ select count(*) from public.fans $$;

revoke all on function public.join_fanclub(text, text, boolean) from public;
revoke all on function public.fan_count() from public;
grant execute on function public.join_fanclub(text, text, boolean) to anon, authenticated;
grant execute on function public.fan_count() to anon, authenticated;

-- Run once in the Supabase SQL editor (Dashboard → SQL Editor → New query → Run).
-- Safe to re-run. Then load the knowledge base:  python data/load_knowledge_base.py

create extension if not exists vector;


-- 1. Knowledge base: one row per curated concept, embedded for semantic search.
create table if not exists public.rag_concepts (
  id               text primary key,
  concept          text not null,
  text             text not null,
  domain           text not null,
  subdomain        text not null,
  difficulty       text not null check (difficulty in ('L1', 'L2', 'L3')),
  core_signals     text[] not null default '{}',
  advanced_signals text[] not null default '{}',
  misconceptions   text[] not null default '{}',
  embedding        vector(768)
);

create index if not exists rag_concepts_difficulty_domain_idx on public.rag_concepts (difficulty, domain);


-- 2. Interview sessions. Config and adaptive state are JSONB so one row holds
--    everything needed to resume or report on an interview.
create table if not exists public.interviews (
  id             text primary key,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  status         text not null check (status in ('created', 'in_progress', 'completed')),
  is_sample      boolean not null default false,
  candidate_name text not null,
  role           text not null,
  config         jsonb not null,
  state          jsonb not null,
  report         jsonb
);

create index if not exists interviews_created_at_idx on public.interviews (created_at desc);


-- 3. Only the backend talks to these tables, using a secret key (which bypasses
--    RLS). With RLS on and no policies, publishable/anon keys get no access.
alter table public.rag_concepts enable row level security;
alter table public.interviews enable row level security;


-- 4. Vector search. Both return ids only; the backend keeps the concept catalog in memory.
--    (With 127 rows an exact scan is fast; add an HNSW index if the knowledge base grows.)
create or replace function public.match_concepts_filtered(
  query_embedding vector(768),
  match_difficulty text,
  match_domains text[] default null,
  exclude_ids text[] default '{}',
  match_count int default 5
)
returns table (id text, similarity float)
language sql stable
as $$
  select c.id, 1 - (c.embedding <=> query_embedding) as similarity
  from public.rag_concepts c
  where c.embedding is not null
    and c.difficulty = match_difficulty
    and (match_domains is null or c.domain = any (match_domains))
    and not (c.id = any (coalesce(exclude_ids, '{}')))
  order by c.embedding <=> query_embedding
  limit match_count;
$$;

-- The original RPC signature, kept for compatibility with the first version of the engine.
create or replace function public.match_concepts(
  query_embedding vector(768),
  match_difficulty text,
  exclude_ids text[] default '{}',
  match_count int default 5
)
returns table (id text, similarity float)
language sql stable
as $$
  select * from public.match_concepts_filtered(query_embedding, match_difficulty, null, exclude_ids, match_count);
$$;

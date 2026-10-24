-- Knowledge base for the Anmeldung helper. Only public, official guidance lives here;
-- no user data is ever stored.
create extension if not exists vector;

create table if not exists sources (
  id           text primary key,
  kind         text not null check (kind in ('statute', 'portal')),
  url          text not null,
  title        text not null,
  publisher    text not null,
  lang         text not null,
  retrieved_at date not null
);

create table if not exists chunks (
  id        text primary key,               -- e.g. 'bmg-17#0'
  source_id text not null references sources(id) on delete cascade,
  lang      text not null,
  section   text not null,
  content   text not null,
  url       text not null,
  embedding vector(768) not null
);

create index if not exists chunks_embedding_idx
  on chunks using hnsw (embedding vector_cosine_ops);

-- No public access: only the backend (service role, which bypasses RLS) reads these tables.
alter table sources enable row level security;
alter table chunks  enable row level security;
revoke all on sources, chunks from anon, authenticated;

create or replace function match_chunks(
  query_embedding vector(768),
  match_count int default 5
)
returns table (
  id text, source_id text, title text, section text, content text, url text, similarity float
)
language sql stable
as $$
  select c.id, c.source_id, s.title, c.section, c.content, c.url,
         1 - (c.embedding <=> query_embedding) as similarity
  from chunks c
  join sources s on s.id = c.source_id
  order by c.embedding <=> query_embedding
  limit match_count;
$$;

revoke execute on function match_chunks(vector, int) from public, anon, authenticated;
grant execute on function match_chunks(vector, int) to service_role;

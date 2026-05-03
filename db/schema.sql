-- ═══════════════════════════════════════════════════════════════════
-- Alibabot — Schéma DB Supabase (Phase 2A)
-- À exécuter dans le SQL Editor Supabase une seule fois.
-- ═══════════════════════════════════════════════════════════════════

-- Extension utile pour les UUID
create extension if not exists "uuid-ossp";

-- ─── Table snapshots ───────────────────────────────────────────────
create table if not exists catalog_snapshots (
    id              uuid primary key default uuid_generate_v4(),
    snapshot_id     text not null unique,        -- ex: '2026-05-03T17-34-48'
    created_at      timestamptz not null default now(),
    started_at      timestamptz not null,
    finished_at     timestamptz not null,
    status          text not null default 'pending'
                       check (status in ('pending', 'active', 'rejected', 'archived')),
    triggered_by    text not null default 'cron'
                       check (triggered_by in ('cron', 'manual', 'cli_push')),
    stats           jsonb not null default '{}'::jsonb,
    error_log       jsonb not null default '[]'::jsonb,
    activated_at    timestamptz,
    activated_by    text,
    notes           text
);

create index if not exists idx_snapshots_status on catalog_snapshots(status);
create index if not exists idx_snapshots_created on catalog_snapshots(created_at desc);

-- ─── Table items ───────────────────────────────────────────────────
create table if not exists catalog_items (
    id              uuid primary key default uuid_generate_v4(),
    snapshot_id     uuid not null references catalog_snapshots(id) on delete cascade,
    supplier        text not null,
    supplier_ref    text not null,
    name            text not null,
    brand           text,
    category        text not null,
    subcategory     text,
    description     text,
    price_eur       numeric(10, 2),
    price_min_eur   numeric(10, 2),
    price_max_eur   numeric(10, 2),
    currency        text default 'EUR',
    in_stock        boolean default true,
    product_url     text not null,
    image_url       text,
    variants        jsonb default '[]'::jsonb,
    tags            jsonb default '[]'::jsonb,
    raw             jsonb default '{}'::jsonb,
    scraped_at      timestamptz,
    constraint uniq_snapshot_supplier_ref unique(snapshot_id, supplier, supplier_ref)
);

create index if not exists idx_items_snapshot on catalog_items(snapshot_id);
create index if not exists idx_items_supplier on catalog_items(supplier);
create index if not exists idx_items_category on catalog_items(category);
create index if not exists idx_items_brand on catalog_items(brand);
create index if not exists idx_items_in_stock on catalog_items(in_stock);

-- ─── Vue : items du snapshot actif ─────────────────────────────────
create or replace view catalog_active_items as
select i.*
from catalog_items i
inner join catalog_snapshots s on s.id = i.snapshot_id
where s.status = 'active';

-- ─── Fonction : purger les snapshots obsolètes ─────────────────────
create or replace function purge_old_snapshots()
returns table(deleted_count int, deleted_status text) as $$
declare
    rejected_deleted int;
    pending_deleted int;
begin
    delete from catalog_snapshots
    where status = 'rejected' and created_at < now() - interval '7 days';
    get diagnostics rejected_deleted = row_count;

    delete from catalog_snapshots
    where status = 'pending' and created_at < now() - interval '7 days';
    get diagnostics pending_deleted = row_count;

    return query
    select rejected_deleted, 'rejected'::text
    union all
    select pending_deleted, 'pending'::text;
end;
$$ language plpgsql security definer;

-- ─── RLS : on garde les tables privées (pas d'accès anon) ──────────
-- Pour la Phase 2A, seules les opérations service_role sont autorisées.
-- Les policies pour l'API (Phase 2B) seront ajoutées plus tard.
alter table catalog_snapshots enable row level security;
alter table catalog_items enable row level security;

-- (Pas de policies = aucune ligne accessible par défaut, sauf service_role)

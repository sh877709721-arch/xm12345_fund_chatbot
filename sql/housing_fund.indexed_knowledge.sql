drop table housing_fund.indexed_knowledge

CREATE TABLE IF NOT EXISTS housing_fund.indexed_knowledge
(
    id bigserial,
    knowledge_id bigint,
    knowledge_type knowledgetypeenum,
    title text COLLATE pg_catalog."default",
    category_level_1 text COLLATE pg_catalog."default",
    category_level_2 text COLLATE pg_catalog."default",
    category_level_3 text COLLATE pg_catalog."default",
    content text COLLATE pg_catalog."default" NOT NULL,
    q_embedding vector(1024),
    a_embedding vector(1024),
    reference text COLLATE pg_catalog."default",
    fts tsvector,
	status varchar(255) default 'A',
	created_time timestamp default now(),
	updated_time timestamp default now()
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS housing_fund.indexed_knowledge
    OWNER to housing_fund.

GRANT ALL ON TABLE housing_fund.indexed_knowledge TO housing_fund.

GRANT ALL ON TABLE housing_fund.indexed_knowledge TO etl;
-- Index: idx_housing_fund.doc_knowledge_fts

-- DROP INDEX IF EXISTS housing_fund.idx_housing_fund.doc_knowledge_fts;

CREATE INDEX IF NOT EXISTS idx_housing_fund.indexed_knowledge_fts
    ON housing_fund.indexed_knowledge USING gin
    (fts)
    TABLESPACE pg_default;
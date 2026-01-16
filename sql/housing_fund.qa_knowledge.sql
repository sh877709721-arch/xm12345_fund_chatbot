-- Table: housing_fund.qa_knowledge

DROP TABLE IF EXISTS housing_fund.qa_knowledge;

CREATE TABLE IF NOT EXISTS housing_fund.qa_knowledge
(
    id bigserial,
	qa_id bigint,
    question text COLLATE pg_catalog."default",
    category_level_1 text COLLATE pg_catalog."default",
    category_level_2 text COLLATE pg_catalog."default",
    category_level_3 text COLLATE pg_catalog."default",
    content text COLLATE pg_catalog."default" NOT NULL,
    q_embedding vector(1024),
    a_embedding vector(1024),
    reference text COLLATE pg_catalog."default",
    fts tsvector,
    CONSTRAINT qa_knowledge_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS housing_fund.qa_knowledge
    OWNER to housing_fund.

GRANT ALL ON TABLE housing_fund.qa_knowledge TO housing_fund.

GRANT ALL ON TABLE housing_fund.qa_knowledge TO etl;
-- Index: idx_housing_fund.qa_knowledge_fts

-- DROP INDEX IF EXISTS housing_fund.idx_housing_fund.qa_knowledge_fts;

CREATE INDEX IF NOT EXISTS idx_housing_fund.qa_knowledge_fts
    ON housing_fund.qa_knowledge USING gin
    (fts)
    TABLESPACE pg_default;
-- Index: idx_fts

-- DROP INDEX IF EXISTS housing_fund.idx_fts;

CREATE INDEX IF NOT EXISTS idx_fts
    ON housing_fund.qa_knowledge USING gin
    (fts)
    TABLESPACE pg_default;

grant all on sequence housing_fund.qa_knowledge_id_seq to etl;
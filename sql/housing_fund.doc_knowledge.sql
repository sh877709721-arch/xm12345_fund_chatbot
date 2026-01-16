-- Table: housing_fund.doc_knowledge

-- DROP TABLE IF EXISTS housing_fund.doc_knowledge;

CREATE TABLE IF NOT EXISTS housing_fund.doc_knowledge
(
    id integer NOT NULL DEFAULT nextval('housing_fund.doc_knowledge_id_seq'::regclass),
    doc_id bigint,
    title text COLLATE pg_catalog."default",
    category_level_1 text COLLATE pg_catalog."default",
    category_level_2 text COLLATE pg_catalog."default",
    category_level_3 text COLLATE pg_catalog."default",
    content text COLLATE pg_catalog."default" NOT NULL,
    q_embedding vector(1024),
    a_embedding vector(1024),
    reference text COLLATE pg_catalog."default",
    fts tsvector,
    CONSTRAINT doc_knowledge_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS housing_fund.doc_knowledge
    OWNER to housing_fund.

GRANT ALL ON TABLE housing_fund.doc_knowledge TO housing_fund.

GRANT ALL ON TABLE housing_fund.doc_knowledge TO etl;


ALTER TABLE IF EXISTS housing_fund.qa_knowledge
    OWNER to etl;


CREATE INDEX IF NOT EXISTS idx_housing_fund.doc_knowledge_fts
    ON housing_fund.doc_knowledge USING gin
    (fts)
    TABLESPACE pg_default;
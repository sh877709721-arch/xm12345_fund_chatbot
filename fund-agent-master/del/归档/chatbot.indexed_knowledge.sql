drop table chatbot.indexed_knowledge

CREATE TABLE IF NOT EXISTS chatbot.indexed_knowledge
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

ALTER TABLE IF EXISTS chatbot.indexed_knowledge
    OWNER to chatbot;

GRANT ALL ON TABLE chatbot.indexed_knowledge TO chatbot;

GRANT ALL ON TABLE chatbot.indexed_knowledge TO etl;
-- Index: idx_chatbot_doc_knowledge_fts

-- DROP INDEX IF EXISTS chatbot.idx_chatbot_doc_knowledge_fts;

CREATE INDEX IF NOT EXISTS idx_chatbot_indexed_knowledge_fts
    ON chatbot.indexed_knowledge USING gin
    (fts)
    TABLESPACE pg_default;
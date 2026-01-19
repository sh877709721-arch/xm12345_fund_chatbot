-- Table: chatbot.qa_knowledge

DROP TABLE IF EXISTS chatbot.qa_knowledge;

CREATE TABLE IF NOT EXISTS chatbot.qa_knowledge
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

ALTER TABLE IF EXISTS chatbot.qa_knowledge
    OWNER to chatbot;

GRANT ALL ON TABLE chatbot.qa_knowledge TO chatbot;

GRANT ALL ON TABLE chatbot.qa_knowledge TO etl;
-- Index: idx_chatbot_qa_knowledge_fts

-- DROP INDEX IF EXISTS chatbot.idx_chatbot_qa_knowledge_fts;

CREATE INDEX IF NOT EXISTS idx_chatbot_qa_knowledge_fts
    ON chatbot.qa_knowledge USING gin
    (fts)
    TABLESPACE pg_default;
-- Index: idx_fts

-- DROP INDEX IF EXISTS chatbot.idx_fts;

CREATE INDEX IF NOT EXISTS idx_fts
    ON chatbot.qa_knowledge USING gin
    (fts)
    TABLESPACE pg_default;

grant all on sequence chatbot.qa_knowledge_id_seq to etl;
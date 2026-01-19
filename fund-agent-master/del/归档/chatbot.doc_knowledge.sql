-- Table: chatbot.doc_knowledge

-- DROP TABLE IF EXISTS chatbot.doc_knowledge;

CREATE TABLE IF NOT EXISTS chatbot.doc_knowledge
(
    id integer NOT NULL DEFAULT nextval('chatbot.doc_knowledge_id_seq'::regclass),
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

ALTER TABLE IF EXISTS chatbot.doc_knowledge
    OWNER to chatbot;

GRANT ALL ON TABLE chatbot.doc_knowledge TO chatbot;

GRANT ALL ON TABLE chatbot.doc_knowledge TO etl;


ALTER TABLE IF EXISTS chatbot.qa_knowledge
    OWNER to etl;


CREATE INDEX IF NOT EXISTS idx_chatbot_doc_knowledge_fts
    ON chatbot.doc_knowledge USING gin
    (fts)
    TABLESPACE pg_default;
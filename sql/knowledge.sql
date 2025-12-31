/*
chatbot.knowledge_catalog
*/
CREATE TABLE IF NOT EXISTS chatbot.knowledge_catalog
(
    id integer NOT NULL DEFAULT nextval('knowledge_catalog_id_seq'::regclass),
    category_level_1 character varying(255) COLLATE pg_catalog."default",
    category_level_2 character varying(255) COLLATE pg_catalog."default",
    category_level_3 character varying(255) COLLATE pg_catalog."default",
    status knowledgestatusenum NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    CONSTRAINT knowledge_catalog_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS chatbot.knowledge_catalog
    OWNER to chatbot;

GRANT ALL ON TABLE chatbot.knowledge_catalog TO chatbot;

GRANT ALL ON TABLE chatbot.knowledge_catalog TO etl;


/*
chatbot.knowledge
*/

-- Table: chatbot.knowledge

-- DROP TABLE IF EXISTS chatbot.knowledge;

CREATE TABLE IF NOT EXISTS chatbot.knowledge
(
    id bigint NOT NULL DEFAULT nextval('knowledge_id_seq'::regclass),
    knowledge_type knowledgetypeenum NOT NULL,
    knowledge_catalog_id bigint,
    name character varying(255) COLLATE pg_catalog."default",
    status knowledgestatusenum NOT NULL,
    created_by bigint,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    CONSTRAINT knowledge_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS chatbot.knowledge
    OWNER to chatbot;




-- Table: chatbot.knowledge_detail

-- DROP TABLE IF EXISTS chatbot.knowledge_detail;

CREATE TABLE IF NOT EXISTS chatbot.knowledge_detail
(
    id bigint NOT NULL DEFAULT nextval('knowledge_detail_id_seq'::regclass),
    knowledge_id bigint,
    content text COLLATE pg_catalog."default",
    status knowledgestatusenum NOT NULL,
    role character varying(255) COLLATE pg_catalog."default",
    reference text COLLATE pg_catalog."default",
    version bigint,
    created_by bigint,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    CONSTRAINT knowledge_detail_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS chatbot.knowledge_detail
    OWNER to chatbot;



update chatbot.knowledge_detail 
set status ='active'
where status = 'pending'

update chatbot.knowledge 
set status ='active'
where status = 'pending'
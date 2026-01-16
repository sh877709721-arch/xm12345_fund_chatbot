/*
housing_fund.knowledge_catalog
*/
CREATE TABLE IF NOT EXISTS housing_fund.knowledge_catalog
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

ALTER TABLE IF EXISTS housing_fund.knowledge_catalog
    OWNER to housing_fund.

GRANT ALL ON TABLE housing_fund.knowledge_catalog TO housing_fund.

GRANT ALL ON TABLE housing_fund.knowledge_catalog TO etl;


/*
housing_fund.knowledge
*/

-- Table: housing_fund.knowledge

-- DROP TABLE IF EXISTS housing_fund.knowledge;

CREATE TABLE IF NOT EXISTS housing_fund.knowledge
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

ALTER TABLE IF EXISTS housing_fund.knowledge
    OWNER to housing_fund.




-- Table: housing_fund.knowledge_detail

-- DROP TABLE IF EXISTS housing_fund.knowledge_detail;

CREATE TABLE IF NOT EXISTS housing_fund.knowledge_detail
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

ALTER TABLE IF EXISTS housing_fund.knowledge_detail
    OWNER to housing_fund.



update housing_fund.knowledge_detail 
set status ='active'
where status = 'pending'

update housing_fund.knowledge 
set status ='active'
where status = 'pending'
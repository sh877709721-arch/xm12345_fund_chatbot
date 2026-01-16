/**
 如果要迁移到其他场景
 将 housing_fund 替换为其他schema即可

**/

-- DROP TABLE housing_fund.chats;

CREATE TABLE housing_fund.chats (
	id uuid NOT NULL,
	title varchar(255) NULL,
	user_id varchar(255) NOT NULL,
	status  varchar(255) NOT NULL default 'active',  --active
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT chats_pkey PRIMARY KEY (id)
);

-- DROP TABLE housing_fund.users;
CREATE TABLE housing_fund.users
(
    id bigserial not null,
    username character varying(255) COLLATE pg_catalog."default" NOT NULL,
    email character varying(255) COLLATE pg_catalog."default" NOT NULL,
    hashed_password character varying(255) COLLATE pg_catalog."default" NOT NULL,
    full_name character varying(255) COLLATE pg_catalog."default",
	user_role character varying(255) DEFAULT 'normal_user',
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_email_key UNIQUE (email),
    CONSTRAINT users_username_key UNIQUE (username)
);

--DROP TABLE housing_fund.user_roles;

CREATE TABLE housing_fund.user_roles (
	id bigserial NOT NULL,
	user_id bigserial NOT NULL,
	status varchar(255) DEFAULT 'A'::character varying NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
	updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
	role varchar(255) DEFAULT 'normal_user',
	CONSTRAINT user_roles_pkey PRIMARY KEY (id)
);

--DROP TABLE housing_fund.knowledge_catalog;
CREATE TABLE housing_fund.knowledge_catalog(
	id serial4 NOT NULL,
	category_level_1 varchar(255) NULL,
	category_level_2 varchar(255) NULL,
	category_level_3 varchar(255) NULL,
	status varchar(255) NOT NULL default 'active',
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
	updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
	CONSTRAINT knowledge_catalog_pkey PRIMARY KEY (id)
);
INSERT INTO housing_fund.knowledge_catalog(category_level_1,category_level_2,category_level_3)
values ('默认','默认','默认');



-- DROP TABLE housing_fund.knowledge;

CREATE TABLE housing_fund.knowledge (
	id bigserial NOT NULL,
	knowledge_catalog_id int8 NULL,
	name varchar(255) NULL,
	knowledge_type varchar(255) default 'qa', --qa document data_table
    status varchar(255) NOT NULL DEFAULT 'pending', -- pending
	created_by int8 NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT knowledge_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_housing_fund_knowledge_catalog_id ON housing_fund.knowledge USING btree (knowledge_catalog_id);


--DROP TABLE housing_fund.knowledge_detail;
CREATE TABLE housing_fund.knowledge_detail (
	id bigserial NOT NULL,
	knowledge_id int8 NULL,
	content text NULL,
	status varchar(255) NOT NULL DEFAULT 'pending',
	role varchar(255) NULL,
	reference text NULL,
	version int8 NULL,
	filled_by varchar(255) NULL,
	created_by int8 NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT knowledge_detail_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_housing_fund_knowledge_detail_knowledge_id ON housing_fund.knowledge_detail USING btree (knowledge_id);


--DROP TABLE housing_fund.indexed_knowledge;

CREATE TABLE housing_fund.indexed_knowledge (
	id bigserial NOT NULL,
	knowledge_id int8 NULL,
	title text NULL,
	knowledge_type varchar(255) NOT NULL  default 'qa',
	category_level_1 text NULL,
	category_level_2 text NULL,
	category_level_3 text NULL,
	content text NOT NULL,
	q_embedding public.vector(1024) NULL,
	a_embedding public.vector(1024) NULL,
	reference text NULL,
	fts tsvector NULL,
	status varchar(255) DEFAULT 'A'::character varying NULL,
	created_time timestamp DEFAULT now() NULL,
	updated_time timestamp DEFAULT now() NULL
);
CREATE INDEX indexed_knowledge_a_embedding_idx ON housing_fund.indexed_knowledge USING hnsw (a_embedding vector_cosine_ops);
CREATE INDEX indexed_knowledge_q_embedding_idx ON housing_fund.indexed_knowledge USING hnsw (q_embedding vector_cosine_ops);


--DROP TABLE housing_fund.knowledge_data;
CREATE TABLE housing_fund.knowledge_data (
	id bigserial NOT NULL,
	knowledge_id int8 NULL,
	content jsonb NULL,
	fts_content tsvector NULL,
	fts_vector public.vector(1024) NULL,
	status varchar(255) NULL,
	created_by int8 NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT knowledge_data_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_housing_fund_indexed_knowledge_fts ON housing_fund.knowledge_data USING gin (fts_content);
CREATE INDEX idx_housing_fund_knowledge_data_knowledge_id ON housing_fund.knowledge_data USING btree (knowledge_id);




-- housing_fund.message_context definition

-- Drop table

-- DROP TABLE housing_fund.message_context;

/*
 * context_type
 * class ContextType(PyEnum):
    thought = "thought"
    observation = "observation"
    action = "action"
    summary = "summary"  #历史对话的总结
    question = "question" #你可能想问
 * 
 * */

CREATE TABLE housing_fund.message_context (
	id bigserial NOT NULL,
	chat_id uuid NULL,
	message_id int8 NULL,
	context text NULL,
	context_type varchar(255) not null default 'question',
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT message_context_pkey PRIMARY KEY (id)
);


-- housing_fund.messages definition

-- Drop table

-- DROP TABLE housing_fund.messages;

CREATE TABLE housing_fund.messages (
	id bigserial NOT NULL,
	chat_id uuid NULL,
	message_role_enum varchar(255) not null default 'user', --assistant
	content text NULL,
	metadata_ jsonb NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT messages_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_housing_fund_messages_chat_id ON housing_fund.messages USING btree (chat_id);
CREATE INDEX idx_housing_fund_messages_id ON housing_fund.messages USING btree (id);


-- housing_fund.message_context foreign keys

ALTER TABLE housing_fund.message_context ADD CONSTRAINT message_context_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES housing_fund.chats(id);


-- housing_fund.messages foreign keys

ALTER TABLE housing_fund.messages ADD CONSTRAINT messages_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES housing_fund.chats(id);




-- DROP TABLE housing_fund.feedback;

CREATE TABLE housing_fund.feedback (
	id serial4 NOT NULL,
	content text NOT NULL,
	images jsonb NULL,
	phone text NULL,
	status varchar(255) DEFAULT 'A'::character varying NOT NULL,
	created_time timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
	updated_time timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL
);


-- housing_fund.guidelines definition

-- Drop table

-- DROP TABLE housing_fund.guidelines;

CREATE TABLE housing_fund.guidelines (
	id bigserial,
	title varchar(512) NOT NULL,
	condition text NOT NULL,
	action text NOT NULL,
	prompt_template text NULL,
	condition_embedding public.vector(1024) NULL,
	condition_fts tsvector NULL,
	priority int8 NULL,
	status varchar(255) DEFAULT 'A'::character varying NOT NULL,
	created_time timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	updated_time timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	CONSTRAINT guidelines_pkey PRIMARY KEY (id)
);
CREATE INDEX guidelines_condition_embedding_idx ON housing_fund.guidelines USING hnsw (condition_embedding vector_cosine_ops) WITH (m='16', ef_construction='64');
CREATE INDEX idx_condition_fts ON housing_fund.guidelines USING gin (condition_fts);
CREATE INDEX idx_guidelines_created_time ON housing_fund.guidelines USING btree (created_time DESC);
CREATE INDEX idx_guidelines_status ON housing_fund.guidelines USING btree (status);


-- housing_fund.vote definition

-- Drop table

-- DROP TABLE housing_fund.vote;

CREATE TABLE housing_fund.vote (
	vote_id int8 GENERATED BY DEFAULT AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE) NOT NULL,
	message_id int8 NULL, 
    vote_type varchar(255) default 'good', ---good medium bad unknown
	feedback text NULL,  
	created_at timestamp DEFAULT now() NULL,
	updated_at timestamp DEFAULT now() NULL,
	CONSTRAINT vote_pkey PRIMARY KEY (vote_id)
);
CREATE INDEX idx_housing_fund_vote_messages_id ON housing_fund.vote USING btree (message_id);
-- housing_fund.vote foreign keys
ALTER TABLE housing_fund.vote ADD CONSTRAINT vote_message_id_fkey FOREIGN KEY (message_id) REFERENCES housing_fund.messages(id);
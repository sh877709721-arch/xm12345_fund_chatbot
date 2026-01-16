-- housing_fund.alembic_version definition

-- Drop table

-- DROP TABLE housing_fund.alembic_version;

CREATE TABLE housing_fund.alembic_version (
	version_num varchar(32) NOT NULL,
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);


-- housing_fund.chats definition

-- Drop table

-- DROP TABLE housing_fund.chats;

CREATE TABLE housing_fund.chats (
	id uuid NOT NULL,
	title varchar(255) NULL,
	status housing_fund."chatstatusenum" NOT NULL,
	user_id varchar(255) NOT NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT chats_pkey PRIMARY KEY (id)
);


-- housing_fund.doc_knowledge definition

-- Drop table

-- DROP TABLE housing_fund.doc_knowledge;

CREATE TABLE housing_fund.doc_knowledge (
	id serial4 NOT NULL,
	doc_id int8 NULL,
	title text NULL,
	category_level_1 text NULL,
	category_level_2 text NULL,
	category_level_3 text NULL,
	"content" text NOT NULL,
	q_embedding public.vector NULL,
	a_embedding public.vector NULL,
	reference text NULL,
	fts tsvector NULL,
	CONSTRAINT doc_knowledge_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_housing_fund.doc_knowledge_fts ON housing_fund.doc_knowledge USING gin (fts);


-- housing_fund.doc_terms definition

-- Drop table

-- DROP TABLE housing_fund.doc_terms;

CREATE TABLE housing_fund.doc_terms (
	id int4 NULL,
	term text NULL,
	cnt int4 NULL
);


-- housing_fund.feedback definition

-- Drop table

-- DROP TABLE housing_fund.feedback;

CREATE TABLE housing_fund.feedback (
	id serial4 NOT NULL,
	"content" text NOT NULL,
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
	id int8 GENERATED ALWAYS AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE) NOT NULL,
	title varchar(512) NOT NULL,
	"condition" text NOT NULL,
	"action" text NOT NULL,
	prompt_template text NULL,
	condition_embedding public.vector NULL,
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


-- housing_fund.indexed_knowledge definition

-- Drop table

-- DROP TABLE housing_fund.indexed_knowledge;

CREATE TABLE housing_fund.indexed_knowledge (
	id bigserial NOT NULL,
	knowledge_id int8 NULL,
	knowledge_type housing_fund."knowledgetypeenum" NULL,
	title text NULL,
	category_level_1 text NULL,
	category_level_2 text NULL,
	category_level_3 text NULL,
	"content" text NOT NULL,
	q_embedding public.vector NULL,
	a_embedding public.vector NULL,
	reference text NULL,
	fts tsvector NULL,
	status varchar(255) DEFAULT 'A'::character varying NULL,
	created_time timestamp DEFAULT now() NULL,
	updated_time timestamp DEFAULT now() NULL
);
CREATE INDEX indexed_knowledge_a_embedding_idx ON housing_fund.indexed_knowledge USING hnsw (a_embedding vector_cosine_ops);
CREATE INDEX indexed_knowledge_q_embedding_idx ON housing_fund.indexed_knowledge USING hnsw (q_embedding vector_cosine_ops);


-- housing_fund.knowledge definition

-- Drop table

-- DROP TABLE housing_fund.knowledge;

CREATE TABLE housing_fund.knowledge (
	id bigserial NOT NULL,
	knowledge_type housing_fund."knowledgetypeenum" NOT NULL,
	knowledge_catalog_id int8 NULL,
	"name" varchar(255) NULL,
	status housing_fund."knowledgestatusenum" NOT NULL,
	created_by int8 NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	old_id int8 NULL,
	CONSTRAINT knowledge_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_housing_fund.knowledge_catalog_id ON housing_fund.knowledge USING btree (knowledge_catalog_id);


-- housing_fund.knowledge_catalog definition

-- Drop table

-- DROP TABLE housing_fund.knowledge_catalog;

CREATE TABLE housing_fund.knowledge_catalog (
	id serial4 NOT NULL,
	category_level_1 varchar(255) NULL,
	category_level_2 varchar(255) NULL,
	category_level_3 varchar(255) NULL,
	status housing_fund."knowledgestatusenum" NOT NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT knowledge_catalog_pkey PRIMARY KEY (id)
);


-- housing_fund.knowledge_data definition

-- Drop table

-- DROP TABLE housing_fund.knowledge_data;

CREATE TABLE housing_fund.knowledge_data (
	id bigserial NOT NULL,
	knowledge_id int8 NULL,
	"content" jsonb NULL,
	fts_content tsvector NULL,
	status housing_fund."knowledgestatusenum" NOT NULL,
	created_by int8 NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT knowledge_data_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_housing_fund.indexed_knowledge_fts ON housing_fund.knowledge_data USING gin (fts_content);
CREATE INDEX idx_housing_fund.knowledge_data_knowledge_id ON housing_fund.knowledge_data USING btree (knowledge_id);


-- housing_fund.knowledge_detail definition

-- Drop table

-- DROP TABLE housing_fund.knowledge_detail;

CREATE TABLE housing_fund.knowledge_detail (
	id bigserial NOT NULL,
	knowledge_id int8 NULL,
	"content" text NULL,
	status housing_fund."knowledgestatusenum" NOT NULL,
	"role" varchar(255) NULL,
	reference text NULL,
	"version" int8 NULL,
	filled_by varchar(255) NULL,
	created_by int8 NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT knowledge_detail_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_housing_fund.knowledge_detail_knowledge_id ON housing_fund.knowledge_detail USING btree (knowledge_id);


-- housing_fund.knowledge_label_batch definition

-- Drop table

-- DROP TABLE housing_fund.knowledge_label_batch;

CREATE TABLE housing_fund.knowledge_label_batch (
	id serial4 NOT NULL,
	"name" varchar(255) NULL,
	status housing_fund."knowledgestatusenum" NULL,
	created_at timestamp DEFAULT now() NULL,
	updated_at timestamp DEFAULT now() NULL,
	CONSTRAINT knowledge_label_batch_pkey PRIMARY KEY (id)
);


-- housing_fund.qa_knowledge definition

-- Drop table

-- DROP TABLE housing_fund.qa_knowledge;

CREATE TABLE housing_fund.qa_knowledge (
	id bigserial NOT NULL,
	qa_id int8 NULL,
	title text NULL,
	category_level_1 text NULL,
	category_level_2 text NULL,
	category_level_3 text NULL,
	"content" text NOT NULL,
	q_embedding public.vector NULL,
	a_embedding public.vector NULL,
	reference text NULL,
	fts tsvector NULL,
	CONSTRAINT qa_knowledge_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_housing_fund.qa_knowledge_fts ON housing_fund.qa_knowledge USING gin (fts);
CREATE INDEX idx_fts ON housing_fund.qa_knowledge USING gin (fts);


-- housing_fund.user_roles definition

-- Drop table

-- DROP TABLE housing_fund.user_roles;

CREATE TABLE housing_fund.user_roles (
	id bigserial NOT NULL,
	user_id bigserial NOT NULL,
	"role" housing_fund."role_enum" NOT NULL,
	status varchar(255) DEFAULT 'A'::character varying NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
	updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
	CONSTRAINT user_roles_pkey PRIMARY KEY (id)
);


-- housing_fund.users definition

-- Drop table

-- DROP TABLE housing_fund.users;

CREATE TABLE housing_fund.users (
	id bigserial NOT NULL,
	username varchar(255) NOT NULL,
	email varchar(255) NOT NULL,
	hashed_password varchar(255) NOT NULL,
	full_name varchar(255) NULL,
	is_active bool DEFAULT true NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
	updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
	user_role housing_fund."role_enum" NULL,
	CONSTRAINT users_email_key UNIQUE (email),
	CONSTRAINT users_username_key UNIQUE (username)
);


-- housing_fund.knowledge_label definition

-- Drop table

-- DROP TABLE housing_fund.knowledge_label;

CREATE TABLE housing_fund.knowledge_label (
	id serial4 NOT NULL,
	"name" varchar(255) NULL,
	batch_id int8 NOT NULL,
	status housing_fund."knowledgestatusenum" NULL,
	created_by int8 NULL,
	created_at timestamp DEFAULT now() NULL,
	updated_at timestamp DEFAULT now() NULL,
	CONSTRAINT knowledge_label_pkey PRIMARY KEY (id),
	CONSTRAINT knowledge_label_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES housing_fund.knowledge_label_batch(id) ON DELETE CASCADE
);


-- housing_fund.knowledge_label_detail definition

-- Drop table

-- DROP TABLE housing_fund.knowledge_label_detail;

CREATE TABLE housing_fund.knowledge_label_detail (
	id serial4 NOT NULL,
	knowledge_label_id int8 NOT NULL,
	"content" text NULL,
	context text NULL,
	"role" housing_fund."knowledgeroleenum" NULL,
	is_pass bool NULL,
	"version" int8 NULL,
	description text NULL,
	filled_by varchar(255) NULL,
	created_by int8 NULL,
	status housing_fund."knowledgestatusenum" NOT NULL,
	created_at timestamp DEFAULT now() NULL,
	updated_at timestamp DEFAULT now() NULL,
	CONSTRAINT knowledge_label_detail_pkey PRIMARY KEY (id),
	CONSTRAINT knowledge_label_detail_knowledge_label_id_fkey FOREIGN KEY (knowledge_label_id) REFERENCES housing_fund.knowledge_label(id) ON DELETE CASCADE
);
CREATE INDEX idx_housing_fund.knowledge_label_detail_label_id ON housing_fund.knowledge_label_detail USING btree (knowledge_label_id);


-- housing_fund.message_context definition

-- Drop table

-- DROP TABLE housing_fund.message_context;

CREATE TABLE housing_fund.message_context (
	id bigserial NOT NULL,
	chat_id uuid NULL,
	message_id int8 NULL,
	context text NULL,
	context_type housing_fund."contexttype" NOT NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT message_context_pkey PRIMARY KEY (id),
	CONSTRAINT message_context_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES housing_fund.chats(id)
);


-- housing_fund.messages definition

-- Drop table

-- DROP TABLE housing_fund.messages;

CREATE TABLE housing_fund.messages (
	id bigserial NOT NULL,
	chat_id uuid NULL,
	message_role_enum housing_fund."messageroleenum" NOT NULL,
	"content" text NULL,
	metadata_ jsonb NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT messages_pkey PRIMARY KEY (id),
	CONSTRAINT messages_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES housing_fund.chats(id)
);
CREATE INDEX idx_housing_fund.messages_chat_id ON housing_fund.messages USING btree (chat_id);
CREATE INDEX idx_housing_fund.messages_id ON housing_fund.messages USING btree (id);


-- housing_fund.vote definition

-- Drop table

-- DROP TABLE housing_fund.vote;

CREATE TABLE housing_fund.vote (
	vote_id int8 GENERATED BY DEFAULT AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE) NOT NULL,
	message_id int8 NULL,
	"vote_type" housing_fund."vote_type" NOT NULL,
	feedback text NULL,
	created_at timestamp DEFAULT now() NULL,
	updated_at timestamp DEFAULT now() NULL,
	CONSTRAINT vote_pkey PRIMARY KEY (vote_id),
	CONSTRAINT vote_message_id_fkey FOREIGN KEY (message_id) REFERENCES housing_fund.messages(id)
);
CREATE INDEX idx_housing_fund.vote_messages_id ON housing_fund.vote USING btree (message_id);
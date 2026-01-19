-- chatbot.alembic_version definition

-- Drop table

-- DROP TABLE chatbot.alembic_version;

CREATE TABLE chatbot.alembic_version (
	version_num varchar(32) NOT NULL,
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);


-- chatbot.chats definition

-- Drop table

-- DROP TABLE chatbot.chats;

CREATE TABLE chatbot.chats (
	id uuid NOT NULL,
	title varchar(255) NULL,
	status chatbot."chatstatusenum" NOT NULL,
	user_id varchar(255) NOT NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT chats_pkey PRIMARY KEY (id)
);


-- chatbot.doc_knowledge definition

-- Drop table

-- DROP TABLE chatbot.doc_knowledge;

CREATE TABLE chatbot.doc_knowledge (
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
CREATE INDEX idx_chatbot_doc_knowledge_fts ON chatbot.doc_knowledge USING gin (fts);


-- chatbot.doc_terms definition

-- Drop table

-- DROP TABLE chatbot.doc_terms;

CREATE TABLE chatbot.doc_terms (
	id int4 NULL,
	term text NULL,
	cnt int4 NULL
);


-- chatbot.feedback definition

-- Drop table

-- DROP TABLE chatbot.feedback;

CREATE TABLE chatbot.feedback (
	id serial4 NOT NULL,
	"content" text NOT NULL,
	images jsonb NULL,
	phone text NULL,
	status varchar(255) DEFAULT 'A'::character varying NOT NULL,
	created_time timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
	updated_time timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL
);


-- chatbot.guidelines definition

-- Drop table

-- DROP TABLE chatbot.guidelines;

CREATE TABLE chatbot.guidelines (
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
CREATE INDEX guidelines_condition_embedding_idx ON chatbot.guidelines USING hnsw (condition_embedding vector_cosine_ops) WITH (m='16', ef_construction='64');
CREATE INDEX idx_condition_fts ON chatbot.guidelines USING gin (condition_fts);
CREATE INDEX idx_guidelines_created_time ON chatbot.guidelines USING btree (created_time DESC);
CREATE INDEX idx_guidelines_status ON chatbot.guidelines USING btree (status);


-- chatbot.indexed_knowledge definition

-- Drop table

-- DROP TABLE chatbot.indexed_knowledge;

CREATE TABLE chatbot.indexed_knowledge (
	id bigserial NOT NULL,
	knowledge_id int8 NULL,
	knowledge_type chatbot."knowledgetypeenum" NULL,
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
CREATE INDEX indexed_knowledge_a_embedding_idx ON chatbot.indexed_knowledge USING hnsw (a_embedding vector_cosine_ops);
CREATE INDEX indexed_knowledge_q_embedding_idx ON chatbot.indexed_knowledge USING hnsw (q_embedding vector_cosine_ops);


-- chatbot.knowledge definition

-- Drop table

-- DROP TABLE chatbot.knowledge;

CREATE TABLE chatbot.knowledge (
	id bigserial NOT NULL,
	knowledge_type chatbot."knowledgetypeenum" NOT NULL,
	knowledge_catalog_id int8 NULL,
	"name" varchar(255) NULL,
	status chatbot."knowledgestatusenum" NOT NULL,
	created_by int8 NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	old_id int8 NULL,
	CONSTRAINT knowledge_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_chatbot_knowledge_catalog_id ON chatbot.knowledge USING btree (knowledge_catalog_id);


-- chatbot.knowledge_catalog definition

-- Drop table

-- DROP TABLE chatbot.knowledge_catalog;

CREATE TABLE chatbot.knowledge_catalog (
	id serial4 NOT NULL,
	category_level_1 varchar(255) NULL,
	category_level_2 varchar(255) NULL,
	category_level_3 varchar(255) NULL,
	status chatbot."knowledgestatusenum" NOT NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT knowledge_catalog_pkey PRIMARY KEY (id)
);


-- chatbot.knowledge_data definition

-- Drop table

-- DROP TABLE chatbot.knowledge_data;

CREATE TABLE chatbot.knowledge_data (
	id bigserial NOT NULL,
	knowledge_id int8 NULL,
	"content" jsonb NULL,
	fts_content tsvector NULL,
	status chatbot."knowledgestatusenum" NOT NULL,
	created_by int8 NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT knowledge_data_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_chatbot_indexed_knowledge_fts ON chatbot.knowledge_data USING gin (fts_content);
CREATE INDEX idx_chatbot_knowledge_data_knowledge_id ON chatbot.knowledge_data USING btree (knowledge_id);


-- chatbot.knowledge_detail definition

-- Drop table

-- DROP TABLE chatbot.knowledge_detail;

CREATE TABLE chatbot.knowledge_detail (
	id bigserial NOT NULL,
	knowledge_id int8 NULL,
	"content" text NULL,
	status chatbot."knowledgestatusenum" NOT NULL,
	"role" varchar(255) NULL,
	reference text NULL,
	"version" int8 NULL,
	filled_by varchar(255) NULL,
	created_by int8 NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT knowledge_detail_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_chatbot_knowledge_detail_knowledge_id ON chatbot.knowledge_detail USING btree (knowledge_id);


-- chatbot.knowledge_label_batch definition

-- Drop table

-- DROP TABLE chatbot.knowledge_label_batch;

CREATE TABLE chatbot.knowledge_label_batch (
	id serial4 NOT NULL,
	"name" varchar(255) NULL,
	status chatbot."knowledgestatusenum" NULL,
	created_at timestamp DEFAULT now() NULL,
	updated_at timestamp DEFAULT now() NULL,
	CONSTRAINT knowledge_label_batch_pkey PRIMARY KEY (id)
);


-- chatbot.qa_knowledge definition

-- Drop table

-- DROP TABLE chatbot.qa_knowledge;

CREATE TABLE chatbot.qa_knowledge (
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
CREATE INDEX idx_chatbot_qa_knowledge_fts ON chatbot.qa_knowledge USING gin (fts);
CREATE INDEX idx_fts ON chatbot.qa_knowledge USING gin (fts);


-- chatbot.user_roles definition

-- Drop table

-- DROP TABLE chatbot.user_roles;

CREATE TABLE chatbot.user_roles (
	id bigserial NOT NULL,
	user_id bigserial NOT NULL,
	"role" chatbot."role_enum" NOT NULL,
	status varchar(255) DEFAULT 'A'::character varying NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
	updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
	CONSTRAINT user_roles_pkey PRIMARY KEY (id)
);


-- chatbot.users definition

-- Drop table

-- DROP TABLE chatbot.users;

CREATE TABLE chatbot.users (
	id bigserial NOT NULL,
	username varchar(255) NOT NULL,
	email varchar(255) NOT NULL,
	hashed_password varchar(255) NOT NULL,
	full_name varchar(255) NULL,
	is_active bool DEFAULT true NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
	updated_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
	user_role chatbot."role_enum" NULL,
	CONSTRAINT users_email_key UNIQUE (email),
	CONSTRAINT users_username_key UNIQUE (username)
);


-- chatbot.knowledge_label definition

-- Drop table

-- DROP TABLE chatbot.knowledge_label;

CREATE TABLE chatbot.knowledge_label (
	id serial4 NOT NULL,
	"name" varchar(255) NULL,
	batch_id int8 NOT NULL,
	status chatbot."knowledgestatusenum" NULL,
	created_by int8 NULL,
	created_at timestamp DEFAULT now() NULL,
	updated_at timestamp DEFAULT now() NULL,
	CONSTRAINT knowledge_label_pkey PRIMARY KEY (id),
	CONSTRAINT knowledge_label_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES chatbot.knowledge_label_batch(id) ON DELETE CASCADE
);


-- chatbot.knowledge_label_detail definition

-- Drop table

-- DROP TABLE chatbot.knowledge_label_detail;

CREATE TABLE chatbot.knowledge_label_detail (
	id serial4 NOT NULL,
	knowledge_label_id int8 NOT NULL,
	"content" text NULL,
	context text NULL,
	"role" chatbot."knowledgeroleenum" NULL,
	is_pass bool NULL,
	"version" int8 NULL,
	description text NULL,
	filled_by varchar(255) NULL,
	created_by int8 NULL,
	status chatbot."knowledgestatusenum" NOT NULL,
	created_at timestamp DEFAULT now() NULL,
	updated_at timestamp DEFAULT now() NULL,
	CONSTRAINT knowledge_label_detail_pkey PRIMARY KEY (id),
	CONSTRAINT knowledge_label_detail_knowledge_label_id_fkey FOREIGN KEY (knowledge_label_id) REFERENCES chatbot.knowledge_label(id) ON DELETE CASCADE
);
CREATE INDEX idx_chatbot_knowledge_label_detail_label_id ON chatbot.knowledge_label_detail USING btree (knowledge_label_id);


-- chatbot.message_context definition

-- Drop table

-- DROP TABLE chatbot.message_context;

CREATE TABLE chatbot.message_context (
	id bigserial NOT NULL,
	chat_id uuid NULL,
	message_id int8 NULL,
	context text NULL,
	context_type chatbot."contexttype" NOT NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT message_context_pkey PRIMARY KEY (id),
	CONSTRAINT message_context_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES chatbot.chats(id)
);


-- chatbot.messages definition

-- Drop table

-- DROP TABLE chatbot.messages;

CREATE TABLE chatbot.messages (
	id bigserial NOT NULL,
	chat_id uuid NULL,
	message_role_enum chatbot."messageroleenum" NOT NULL,
	"content" text NULL,
	metadata_ jsonb NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT messages_pkey PRIMARY KEY (id),
	CONSTRAINT messages_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES chatbot.chats(id)
);
CREATE INDEX idx_chatbot_messages_chat_id ON chatbot.messages USING btree (chat_id);
CREATE INDEX idx_chatbot_messages_id ON chatbot.messages USING btree (id);


-- chatbot.vote definition

-- Drop table

-- DROP TABLE chatbot.vote;

CREATE TABLE chatbot.vote (
	vote_id int8 GENERATED BY DEFAULT AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE) NOT NULL,
	message_id int8 NULL,
	"vote_type" chatbot."vote_type" NOT NULL,
	feedback text NULL,
	created_at timestamp DEFAULT now() NULL,
	updated_at timestamp DEFAULT now() NULL,
	CONSTRAINT vote_pkey PRIMARY KEY (vote_id),
	CONSTRAINT vote_message_id_fkey FOREIGN KEY (message_id) REFERENCES chatbot.messages(id)
);
CREATE INDEX idx_chatbot_vote_messages_id ON chatbot.vote USING btree (message_id);
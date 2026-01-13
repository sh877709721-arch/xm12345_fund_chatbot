drop table chatbot.knowledge_data;
CREATE TABLE chatbot.knowledge_data(
	id bigserial NOT NULL,
	knowledge_id int8 NULL,
	content jsonb,
	fts_content tsvector NULL,
	status chatbot."knowledgestatusenum" NOT NULL,
	created_by int8 NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT knowledge_data_pkey PRIMARY KEY (id)
);

CREATE INDEX idx_chatbot_knowledge_data_knowledge_id ON chatbot.knowledge_data(knowledge_id);
CREATE INDEX idx_chatbot_indexed_knowledge_fts ON chatbot.knowledge_data USING gin (fts_content);
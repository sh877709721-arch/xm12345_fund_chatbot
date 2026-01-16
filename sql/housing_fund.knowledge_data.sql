drop table housing_fund.knowledge_data;
CREATE TABLE housing_fund.knowledge_data(
	id bigserial NOT NULL,
	knowledge_id int8 NULL,
	content jsonb,
	fts_content tsvector NULL,
	status housing_fund."knowledgestatusenum" NOT NULL,
	created_by int8 NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT knowledge_data_pkey PRIMARY KEY (id)
);

CREATE INDEX idx_housing_fund.knowledge_data_knowledge_id ON housing_fund.knowledge_data(knowledge_id);
CREATE INDEX idx_housing_fund.indexed_knowledge_fts ON housing_fund.knowledge_data USING gin (fts_content);
-- DROP TYPE housing_fund._chatstatusenum;

CREATE TYPE housing_fund._chatstatusenum (
	INPUT = array_in,
	OUTPUT = array_out,
	RECEIVE = array_recv,
	SEND = array_send,
	ANALYZE = array_typanalyze,
	ALIGNMENT = 4,
	STORAGE = any,
	CATEGORY = A,
	ELEMENT = housing_fund."chatstatusenum",
	DELIMITER = ',');

-- DROP TYPE housing_fund._contexttype;

CREATE TYPE housing_fund._contexttype (
	INPUT = array_in,
	OUTPUT = array_out,
	RECEIVE = array_recv,
	SEND = array_send,
	ANALYZE = array_typanalyze,
	ALIGNMENT = 4,
	STORAGE = any,
	CATEGORY = A,
	ELEMENT = housing_fund."contexttype",
	DELIMITER = ',');

-- DROP TYPE housing_fund._knowledgeroleenum;

CREATE TYPE housing_fund._knowledgeroleenum (
	INPUT = array_in,
	OUTPUT = array_out,
	RECEIVE = array_recv,
	SEND = array_send,
	ANALYZE = array_typanalyze,
	ALIGNMENT = 4,
	STORAGE = any,
	CATEGORY = A,
	ELEMENT = housing_fund."knowledgeroleenum",
	DELIMITER = ',');

-- DROP TYPE housing_fund._knowledgestatusenum;

CREATE TYPE housing_fund._knowledgestatusenum (
	INPUT = array_in,
	OUTPUT = array_out,
	RECEIVE = array_recv,
	SEND = array_send,
	ANALYZE = array_typanalyze,
	ALIGNMENT = 4,
	STORAGE = any,
	CATEGORY = A,
	ELEMENT = housing_fund."knowledgestatusenum",
	DELIMITER = ',');

-- DROP TYPE housing_fund._knowledgetypeenum;

CREATE TYPE housing_fund._knowledgetypeenum (
	INPUT = array_in,
	OUTPUT = array_out,
	RECEIVE = array_recv,
	SEND = array_send,
	ANALYZE = array_typanalyze,
	ALIGNMENT = 4,
	STORAGE = any,
	CATEGORY = A,
	ELEMENT = housing_fund."knowledgetypeenum",
	DELIMITER = ',');

-- DROP TYPE housing_fund._messageroleenum;

CREATE TYPE housing_fund._messageroleenum (
	INPUT = array_in,
	OUTPUT = array_out,
	RECEIVE = array_recv,
	SEND = array_send,
	ANALYZE = array_typanalyze,
	ALIGNMENT = 4,
	STORAGE = any,
	CATEGORY = A,
	ELEMENT = housing_fund."messageroleenum",
	DELIMITER = ',');

-- DROP TYPE housing_fund._role_enum;

CREATE TYPE housing_fund._role_enum (
	INPUT = array_in,
	OUTPUT = array_out,
	RECEIVE = array_recv,
	SEND = array_send,
	ANALYZE = array_typanalyze,
	ALIGNMENT = 4,
	STORAGE = any,
	CATEGORY = A,
	ELEMENT = housing_fund."role_enum",
	DELIMITER = ',');

-- DROP TYPE housing_fund._vote_type;

CREATE TYPE housing_fund._vote_type (
	INPUT = array_in,
	OUTPUT = array_out,
	RECEIVE = array_recv,
	SEND = array_send,
	ANALYZE = array_typanalyze,
	ALIGNMENT = 4,
	STORAGE = any,
	CATEGORY = A,
	ELEMENT = housing_fund."vote_type",
	DELIMITER = ',');

-- DROP TYPE housing_fund."chatstatusenum";

CREATE TYPE housing_fund."chatstatusenum" AS ENUM (
	'active',
	'deleted');

-- DROP TYPE housing_fund."contexttype";

CREATE TYPE housing_fund."contexttype" AS ENUM (
	'thought',
	'observation',
	'action',
	'summary',
	'question');

-- DROP TYPE housing_fund."knowledgeroleenum";

CREATE TYPE housing_fund."knowledgeroleenum" AS ENUM (
	'system',
	'user',
	'assistant',
	'admin');

-- DROP TYPE housing_fund."knowledgestatusenum";

CREATE TYPE housing_fund."knowledgestatusenum" AS ENUM (
	'active',
	'deleted',
	'pending',
	'indexing');

-- DROP TYPE housing_fund."knowledgetypeenum";

CREATE TYPE housing_fund."knowledgetypeenum" AS ENUM (
	'document',
	'data_table',
	'qa');

-- DROP TYPE housing_fund."messageroleenum";

CREATE TYPE housing_fund."messageroleenum" AS ENUM (
	'system',
	'user',
	'assistant');

-- DROP TYPE housing_fund."role_enum";

CREATE TYPE housing_fund."role_enum" AS ENUM (
	'superadmin',
	'normal_user',
	'engineer',
	'admin');

-- DROP TYPE housing_fund."vote_type";

CREATE TYPE housing_fund."vote_type" AS ENUM (
	'good',
	'average',
	'poor',
	'middle',
	'bad',
	'medium',
	'unknown');
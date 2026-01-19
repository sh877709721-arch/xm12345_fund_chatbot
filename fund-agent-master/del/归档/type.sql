-- DROP TYPE chatbot._chatstatusenum;

CREATE TYPE chatbot._chatstatusenum (
	INPUT = array_in,
	OUTPUT = array_out,
	RECEIVE = array_recv,
	SEND = array_send,
	ANALYZE = array_typanalyze,
	ALIGNMENT = 4,
	STORAGE = any,
	CATEGORY = A,
	ELEMENT = chatbot."chatstatusenum",
	DELIMITER = ',');

-- DROP TYPE chatbot._contexttype;

CREATE TYPE chatbot._contexttype (
	INPUT = array_in,
	OUTPUT = array_out,
	RECEIVE = array_recv,
	SEND = array_send,
	ANALYZE = array_typanalyze,
	ALIGNMENT = 4,
	STORAGE = any,
	CATEGORY = A,
	ELEMENT = chatbot."contexttype",
	DELIMITER = ',');

-- DROP TYPE chatbot._knowledgeroleenum;

CREATE TYPE chatbot._knowledgeroleenum (
	INPUT = array_in,
	OUTPUT = array_out,
	RECEIVE = array_recv,
	SEND = array_send,
	ANALYZE = array_typanalyze,
	ALIGNMENT = 4,
	STORAGE = any,
	CATEGORY = A,
	ELEMENT = chatbot."knowledgeroleenum",
	DELIMITER = ',');

-- DROP TYPE chatbot._knowledgestatusenum;

CREATE TYPE chatbot._knowledgestatusenum (
	INPUT = array_in,
	OUTPUT = array_out,
	RECEIVE = array_recv,
	SEND = array_send,
	ANALYZE = array_typanalyze,
	ALIGNMENT = 4,
	STORAGE = any,
	CATEGORY = A,
	ELEMENT = chatbot."knowledgestatusenum",
	DELIMITER = ',');

-- DROP TYPE chatbot._knowledgetypeenum;

CREATE TYPE chatbot._knowledgetypeenum (
	INPUT = array_in,
	OUTPUT = array_out,
	RECEIVE = array_recv,
	SEND = array_send,
	ANALYZE = array_typanalyze,
	ALIGNMENT = 4,
	STORAGE = any,
	CATEGORY = A,
	ELEMENT = chatbot."knowledgetypeenum",
	DELIMITER = ',');

-- DROP TYPE chatbot._messageroleenum;

CREATE TYPE chatbot._messageroleenum (
	INPUT = array_in,
	OUTPUT = array_out,
	RECEIVE = array_recv,
	SEND = array_send,
	ANALYZE = array_typanalyze,
	ALIGNMENT = 4,
	STORAGE = any,
	CATEGORY = A,
	ELEMENT = chatbot."messageroleenum",
	DELIMITER = ',');

-- DROP TYPE chatbot._role_enum;

CREATE TYPE chatbot._role_enum (
	INPUT = array_in,
	OUTPUT = array_out,
	RECEIVE = array_recv,
	SEND = array_send,
	ANALYZE = array_typanalyze,
	ALIGNMENT = 4,
	STORAGE = any,
	CATEGORY = A,
	ELEMENT = chatbot."role_enum",
	DELIMITER = ',');

-- DROP TYPE chatbot._vote_type;

CREATE TYPE chatbot._vote_type (
	INPUT = array_in,
	OUTPUT = array_out,
	RECEIVE = array_recv,
	SEND = array_send,
	ANALYZE = array_typanalyze,
	ALIGNMENT = 4,
	STORAGE = any,
	CATEGORY = A,
	ELEMENT = chatbot."vote_type",
	DELIMITER = ',');

-- DROP TYPE chatbot."chatstatusenum";

CREATE TYPE chatbot."chatstatusenum" AS ENUM (
	'active',
	'deleted');

-- DROP TYPE chatbot."contexttype";

CREATE TYPE chatbot."contexttype" AS ENUM (
	'thought',
	'observation',
	'action',
	'summary',
	'question');

-- DROP TYPE chatbot."knowledgeroleenum";

CREATE TYPE chatbot."knowledgeroleenum" AS ENUM (
	'system',
	'user',
	'assistant',
	'admin');

-- DROP TYPE chatbot."knowledgestatusenum";

CREATE TYPE chatbot."knowledgestatusenum" AS ENUM (
	'active',
	'deleted',
	'pending',
	'indexing');

-- DROP TYPE chatbot."knowledgetypeenum";

CREATE TYPE chatbot."knowledgetypeenum" AS ENUM (
	'document',
	'data_table',
	'qa');

-- DROP TYPE chatbot."messageroleenum";

CREATE TYPE chatbot."messageroleenum" AS ENUM (
	'system',
	'user',
	'assistant');

-- DROP TYPE chatbot."role_enum";

CREATE TYPE chatbot."role_enum" AS ENUM (
	'superadmin',
	'normal_user',
	'engineer',
	'admin');

-- DROP TYPE chatbot."vote_type";

CREATE TYPE chatbot."vote_type" AS ENUM (
	'good',
	'average',
	'poor',
	'middle',
	'bad',
	'medium',
	'unknown');
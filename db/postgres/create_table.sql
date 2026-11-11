-- Table: org_account

DROP TABLE IF EXISTS organization_account CASCADE;

CREATE TABLE IF NOT EXISTS organization_account
(
    org_id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    org_name character varying(128) COLLATE pg_catalog."default" NOT NULL,

    created_on timestamp with time zone NOT NULL DEFAULT now(),
    created_by character varying(64) COLLATE pg_catalog."default" NOT NULL,
    updated_on timestamp with time zone NOT NULL DEFAULT now(),
    updated_by character varying(64) COLLATE pg_catalog."default" NOT NULL,

    CONSTRAINT org_pkey PRIMARY KEY (org_id)
)

TABLESPACE pg_default;

INSERT INTO organization_account
    (org_name, created_by, updated_by)
VALUES
    ('root', 'root', 'root');

INSERT INTO organization_account
    (org_name, created_by, updated_by)
VALUES
    ('Demo', 'root', 'root');


-- Table: user_account

DROP TABLE IF EXISTS user_account CASCADE;

CREATE TABLE IF NOT EXISTS user_account
(
    user_id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    org_id bigint NOT NULL,
    user_name character varying(64) COLLATE pg_catalog."default" NOT NULL,
    pass_hash character varying(64) COLLATE pg_catalog."default" NOT NULL,
    user_role character varying(64) COLLATE pg_catalog."default" NOT NULL,
    change_pass boolean NOT NULL DEFAULT false,

    created_on timestamp with time zone NOT NULL DEFAULT now(),
    created_by character varying(64) COLLATE pg_catalog."default" NOT NULL,
    updated_on timestamp with time zone NOT NULL DEFAULT now(),
    updated_by character varying(64) COLLATE pg_catalog."default" NOT NULL,

    CONSTRAINT user_pkey PRIMARY KEY (user_id),
    CONSTRAINT user_user_name_key UNIQUE (user_name),
    CONSTRAINT org_id_org_account_fkey FOREIGN KEY (org_id)
        REFERENCES organization_account (org_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;


DROP INDEX IF EXISTS index_user_login_pass;

CREATE UNIQUE INDEX IF NOT EXISTS index_user_login_pass
    ON user_account USING btree
    (user_name COLLATE pg_catalog."default" ASC NULLS LAST, pass_hash COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;


-- Use the `hash_password` to generate a password hash for the insert statement below:
-- import hashlib
-- def hash_password(password: str) -> str:
--     return hashlib.sha256(password.encode()).hexdigest()
--
INSERT INTO user_account
    (
     org_id, user_name, pass_hash, user_role, change_pass, created_on, created_by, updated_on, updated_by
    )
VALUES
    (
     1,
     'admin',
     'c1f78a0a51c1bb6b1a3e52b2343f6c1ceed92cf436ab53dc4eebc008182739e8',    -- 'ai-agent'
     'Admin',
     false,
     now(),
     'root',
     now(),
     'root'
    );


CREATE TABLE IF NOT EXISTS chat_thread
(
    chat_id     bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     bigint NOT NULL REFERENCES user_account (user_id),
    title       text NOT NULL DEFAULT '',

    created_on timestamp with time zone NOT NULL DEFAULT now(),
    created_by character varying(64) COLLATE pg_catalog."default" NOT NULL default 'admin',
    updated_on timestamp with time zone NOT NULL DEFAULT now(),
    updated_by character varying(64) COLLATE pg_catalog."default" NOT NULL default 'admin'
);

CREATE INDEX IF NOT EXISTS chat_user_updated_idx ON chat_thread (user_id, updated_on);


CREATE TABLE IF NOT EXISTS chat_message
(
    chat_message_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chat_id         bigint NOT NULL REFERENCES chat_thread (chat_id) ON DELETE CASCADE,
    role            varchar(16) NOT NULL,
    content         text NOT NULL,
    sources         jsonb NOT NULL DEFAULT '[]'::jsonb,
    status          varchar(32) NOT NULL DEFAULT '',

    created_on timestamp with time zone NOT NULL DEFAULT now(),
    created_by character varying(64) COLLATE pg_catalog."default" NOT NULL default 'admin',
    updated_on timestamp with time zone NOT NULL DEFAULT now(),
    updated_by character varying(64) COLLATE pg_catalog."default" NOT NULL default 'admin'
);

CREATE INDEX IF NOT EXISTS chat_message_chat_idx ON chat_message (chat_id, chat_message_id);



--------------------------------------------------
--
-- Table: public.user_activity

DROP TABLE IF EXISTS user_activity CASCADE;

CREATE TABLE IF NOT EXISTS user_activity
(
    user_activity_id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    user_id bigint NOT NULL,
    user_name character varying(64) COLLATE pg_catalog."default" NOT NULL,
    user_action character varying(256) COLLATE pg_catalog."default" NOT NULL,

    created_on timestamp with time zone NOT NULL DEFAULT now(),
    created_by character varying(64) COLLATE pg_catalog."default" NOT NULL,

    CONSTRAINT user_activity_pkey PRIMARY KEY (user_activity_id),
    CONSTRAINT user_activity_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES user_account (user_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.user_activity
    OWNER to postgres;


--------------------------------------------------
--
-- Table: public.agent_context

DROP TABLE IF EXISTS public.agent_context CASCADE;

CREATE TABLE IF NOT EXISTS public.agent_context
(
    agent_context_id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    user_id bigint NOT NULL,
    user_name character varying(64) COLLATE pg_catalog."default" NOT NULL,
    context_name TEXT COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    created_by character varying(64) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT agent_context_pkey PRIMARY KEY (agent_context_id),
    CONSTRAINT agent_context_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public.user_account (user_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.agent_context
    OWNER to postgres;


--------------------------------------------------
--
-- Table: public.agent_message

DROP TABLE IF EXISTS public.agent_message CASCADE;

CREATE TABLE IF NOT EXISTS public.agent_message
(
    agent_message_id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    agent_context_id bigint NOT NULL,
    user_id bigint NOT NULL,
    user_name character varying(64) COLLATE pg_catalog."default" NOT NULL,
    role character varying(64) COLLATE pg_catalog."default" NOT NULL,
    content TEXT COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    created_by character varying(64) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT agent_message_pkey PRIMARY KEY (agent_message_id),
    CONSTRAINT agent_message_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public.user_account (user_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT agent_message_context_id_fkey FOREIGN KEY (agent_context_id)
        REFERENCES public.agent_context (agent_context_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.agent_message
    OWNER to postgres;

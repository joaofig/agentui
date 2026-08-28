-- Table: public.user_login

DROP TABLE IF EXISTS public.user_account CASCADE;

CREATE TABLE IF NOT EXISTS public.user_account
(
    user_id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    user_name character varying(64) COLLATE pg_catalog."default" NOT NULL,
    pass_hash character varying(64) COLLATE pg_catalog."default" NOT NULL,
    user_role character varying(64) COLLATE pg_catalog."default" NOT NULL,
    change_pass boolean NOT NULL DEFAULT false,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    created_by character varying(64) COLLATE pg_catalog."default" NOT NULL,
    updated_at timestamp without time zone NOT NULL DEFAULT now(),
    updated_by character varying(64) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT user_pkey PRIMARY KEY (user_id),
    CONSTRAINT user_user_name_key UNIQUE (user_name)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.user_login
    OWNER to postgres;
-- Index: index_user_activity_user_time

DROP INDEX IF EXISTS public.index_user_activity_user_time;

CREATE UNIQUE INDEX IF NOT EXISTS index_user_activity_user_time
    ON public.user_login USING btree
    (user_name COLLATE pg_catalog."default" ASC NULLS LAST, pass_hash COLLATE pg_catalog."default" ASC NULLS LAST, created_at DESC NULLS FIRST)
    TABLESPACE pg_default;
-- Index: index_user_login_pass

DROP INDEX IF EXISTS public.index_user_login_pass;

CREATE UNIQUE INDEX IF NOT EXISTS index_user_login_pass
    ON public.user_login USING btree
    (user_name COLLATE pg_catalog."default" ASC NULLS LAST, pass_hash COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;


INSERT INTO public.user_account
    (
     user_name, pass_hash, user_role, change_pass, created_at, created_by, updated_at, updated_by
    )
VALUES
    (
     'admin',
     'b4074c85261b5b773355468f302cf31d9e4c259d250cad9328f26701ffa47981',
     'Admin',
     false,
     now(),
     'root',
     now(),
     'root'
    );


--------------------------------------------------
--
-- Table: public.user_activity

DROP TABLE IF EXISTS public.user_activity CASCADE;

CREATE TABLE IF NOT EXISTS public.user_activity
(
    user_activity_id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    user_id bigint NOT NULL,
    user_name character varying(64) COLLATE pg_catalog."default" NOT NULL,
    user_action character varying(256) COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    created_by character varying(64) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT user_activity_pkey PRIMARY KEY (user_activity_id),
    CONSTRAINT user_activity_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public.user_account (user_id) MATCH SIMPLE
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
        REFERENCES public.user_login (user_id) MATCH SIMPLE
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
        REFERENCES public.user_login (user_id) MATCH SIMPLE
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

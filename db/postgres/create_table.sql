-- Table: public.user_login

DROP TABLE IF EXISTS public.user_login CASCADE;

CREATE TABLE IF NOT EXISTS public.user_login
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
        REFERENCES public.user_login (user_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.user_activity
    OWNER to postgres;

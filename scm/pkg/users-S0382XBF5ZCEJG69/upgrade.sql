CREATE TABLE public.users (
    id uuid NOT NULL,
    username character varying(100) NOT NULL,
    email character varying NOT NULL,
    normalized_email character varying NOT NULL,
    password_hash character varying NOT NULL,
    auth_type character varying(50) NOT NULL,
    verified boolean NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, statement_timestamp()) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('utc'::text, statement_timestamp()) NOT NULL,
    autogenerated boolean NOT NULL,
    first_name character varying,
    last_name character varying,
    application_id uuid
);

ALTER TABLE ONLY public.users
    ADD CONSTRAINT uq_users_id UNIQUE (id);

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_applications_id FOREIGN KEY (application_id) REFERENCES public.applications(id) ON DELETE CASCADE;

CREATE INDEX ix_users_normalized_email ON public.users USING btree (normalized_email);

CREATE INDEX ix_users_username ON public.users USING btree (username);

CREATE INDEX ix_users_verified ON public.users USING btree (verified);

CREATE UNIQUE INDEX uq_users_normalized_email_application_id ON public.users USING btree (normalized_email, application_id) WHERE (application_id IS NOT NULL);

CREATE UNIQUE INDEX uq_users_normalized_email_no_application_id ON public.users USING btree (normalized_email) WHERE (application_id IS NULL);

CREATE UNIQUE INDEX uq_users_username_application_id ON public.users USING btree (username, application_id) WHERE (application_id IS NOT NULL);

CREATE UNIQUE INDEX uq_users_username_no_application_id ON public.users USING btree (username) WHERE (application_id IS NULL);
CREATE TABLE public.verification_emails (
    id uuid NOT NULL,
    verification_code character varying(6),
    user_id uuid,
    active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, statement_timestamp()) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('utc'::text, statement_timestamp()) NOT NULL
);

ALTER TABLE ONLY public.verification_emails
    ADD CONSTRAINT uq_verification_emails_id UNIQUE (id);

ALTER TABLE ONLY public.verification_emails
    ADD CONSTRAINT verification_emails_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.verification_emails
    ADD CONSTRAINT fk_verification_emails_user_id FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

CREATE INDEX ix_verification_emails_active ON public.verification_emails USING btree (active);

CREATE INDEX ix_verification_emails_user_id ON public.verification_emails USING btree (user_id);

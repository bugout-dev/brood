CREATE TABLE public.reset_passwords (
    id uuid NOT NULL,
    user_id uuid,
    completed boolean NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, statement_timestamp()) NOT NULL
);

ALTER TABLE ONLY public.reset_passwords
    ADD CONSTRAINT pk_reset_passwords PRIMARY KEY (id);

ALTER TABLE ONLY public.reset_passwords
    ADD CONSTRAINT uq_reset_passwords_id UNIQUE (id);

ALTER TABLE ONLY public.reset_passwords
    ADD CONSTRAINT fk_reset_passwords_user_id FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

CREATE INDEX ix_reset_passwords_user_id ON public.reset_passwords USING btree (user_id);

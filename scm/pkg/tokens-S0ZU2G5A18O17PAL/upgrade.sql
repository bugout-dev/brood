CREATE TABLE public.tokens (
    id uuid NOT NULL,
    user_id uuid,
    active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, statement_timestamp()) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('utc'::text, statement_timestamp()) NOT NULL,
    note character varying,
    token_type public.token_type NOT NULL,
    restricted boolean NOT NULL
);

ALTER TABLE ONLY public.tokens
    ADD CONSTRAINT tokens_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.tokens
    ADD CONSTRAINT fk_tokens_user_id FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

CREATE INDEX ix_tokens_active ON public.tokens USING btree (active);

CREATE UNIQUE INDEX ix_tokens_id ON public.tokens USING btree (id);

CREATE INDEX ix_tokens_restricted ON public.tokens USING btree (restricted);

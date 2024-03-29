CREATE TABLE public.groups (
    id uuid NOT NULL,
    autogenerated boolean NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, statement_timestamp()) NOT NULL,
    name character varying(100) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('utc'::text, statement_timestamp()) NOT NULL,
    parent uuid
);

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT pk_groups PRIMARY KEY (id);

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT uq_groups_id UNIQUE (id);

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT fk_groups_parent FOREIGN KEY (parent) REFERENCES public.groups(id) ON DELETE SET NULL;

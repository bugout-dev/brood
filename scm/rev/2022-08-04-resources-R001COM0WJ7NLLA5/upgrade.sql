CREATE TABLE public.resources (
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, statement_timestamp()) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('utc'::text, statement_timestamp()) NOT NULL,
    resource_data jsonb,
    application_id uuid NOT NULL
);

ALTER TABLE ONLY public.resources
    ADD CONSTRAINT pk_resources PRIMARY KEY (id);

ALTER TABLE ONLY public.resources
    ADD CONSTRAINT fk_resources_application_id_applications FOREIGN KEY (application_id) REFERENCES public.applications(id) ON DELETE CASCADE;

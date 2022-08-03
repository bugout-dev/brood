CREATE TABLE public.applications (
    id uuid NOT NULL,
    group_id uuid NOT NULL,
    name character varying NOT NULL,
    description character varying
);

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT pk_applications PRIMARY KEY (id);

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT fk_applications_group_id FOREIGN KEY (group_id) REFERENCES public.groups(id) ON DELETE CASCADE;

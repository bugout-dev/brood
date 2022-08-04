CREATE TABLE public.resource_permissions (
    id uuid NOT NULL,
    resource_id uuid,
    permission character varying NOT NULL
);

ALTER TABLE ONLY public.resource_permissions
    ADD CONSTRAINT pk_resource_permissions PRIMARY KEY (id);

ALTER TABLE ONLY public.resource_permissions
    ADD CONSTRAINT fk_resource_permissions_resource_id_resources FOREIGN KEY (resource_id) REFERENCES public.resources(id) ON DELETE CASCADE;

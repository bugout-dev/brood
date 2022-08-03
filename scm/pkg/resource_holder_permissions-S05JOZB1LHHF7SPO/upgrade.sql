CREATE TABLE public.resource_holder_permissions (
    id uuid NOT NULL,
    user_id uuid,
    group_id uuid,
    resource_id uuid,
    permission_id uuid,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, statement_timestamp()) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('utc'::text, statement_timestamp()) NOT NULL
);

ALTER TABLE ONLY public.resource_holder_permissions
    ADD CONSTRAINT pk_resource_holder_permissions PRIMARY KEY (id);

ALTER TABLE ONLY public.resource_holder_permissions
    ADD CONSTRAINT uq_resource_holder_permissions_user_id UNIQUE (user_id, group_id, resource_id, permission_id);

ALTER TABLE ONLY public.resource_holder_permissions
    ADD CONSTRAINT fk_resource_holder_permissions_group_id_groups FOREIGN KEY (group_id) REFERENCES public.groups(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.resource_holder_permissions
    ADD CONSTRAINT fk_resource_holder_permissions_permission_id_resource_p_4661 FOREIGN KEY (permission_id) REFERENCES public.resource_permissions(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.resource_holder_permissions
    ADD CONSTRAINT fk_resource_holder_permissions_resource_id_resources FOREIGN KEY (resource_id) REFERENCES public.resources(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.resource_holder_permissions
    ADD CONSTRAINT fk_resource_holder_permissions_user_id_users FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

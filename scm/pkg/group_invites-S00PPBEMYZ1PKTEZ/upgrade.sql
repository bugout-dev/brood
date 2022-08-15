CREATE TABLE public.group_invites (
    id uuid NOT NULL,
    group_id uuid NOT NULL,
    initiator_user_id uuid NOT NULL,
    invited_email character varying,
    user_type character varying NOT NULL,
    active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, statement_timestamp()) NOT NULL,
    updated_at timestamp with time zone DEFAULT timezone('utc'::text, statement_timestamp()) NOT NULL
);

ALTER TABLE ONLY public.group_invites
    ADD CONSTRAINT pk_group_invites PRIMARY KEY (id);

ALTER TABLE ONLY public.group_invites
    ADD CONSTRAINT fk_group_invites_group_id FOREIGN KEY (group_id) REFERENCES public.groups(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.group_invites
    ADD CONSTRAINT fk_group_invites_initiator_user_id FOREIGN KEY (initiator_user_id) REFERENCES public.users(id) ON DELETE CASCADE;

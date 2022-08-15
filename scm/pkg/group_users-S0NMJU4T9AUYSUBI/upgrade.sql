CREATE TABLE public.group_users (
    group_id uuid NOT NULL,
    user_id uuid NOT NULL,
    user_type public.user_type NOT NULL
);

ALTER TABLE ONLY public.group_users
    ADD CONSTRAINT pk_group_users PRIMARY KEY (group_id, user_id);

ALTER TABLE ONLY public.group_users
    ADD CONSTRAINT fk_group_users_group_id FOREIGN KEY (group_id) REFERENCES public.groups(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.group_users
    ADD CONSTRAINT fk_group_users_user_id FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

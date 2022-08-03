CREATE TABLE public.user_group_limits (
    id integer NOT NULL,
    user_id uuid NOT NULL,
    group_limit integer NOT NULL
);

CREATE SEQUENCE public.user_group_limits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.user_group_limits_id_seq OWNED BY public.user_group_limits.id;

ALTER TABLE ONLY public.user_group_limits ALTER COLUMN id SET DEFAULT nextval('public.user_group_limits_id_seq'::regclass);

ALTER TABLE ONLY public.user_group_limits
    ADD CONSTRAINT pk_user_group_limits PRIMARY KEY (id);

ALTER TABLE ONLY public.user_group_limits
    ADD CONSTRAINT uq_user_group_limits_user_id UNIQUE (user_id);

ALTER TABLE ONLY public.user_group_limits
    ADD CONSTRAINT fk_user_group_limits_user_id FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

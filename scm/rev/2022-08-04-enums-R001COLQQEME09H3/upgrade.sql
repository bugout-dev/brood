CREATE TYPE public.token_type AS ENUM (
    'bugout',
    'slack',
    'github'
);

CREATE TYPE public.user_type AS ENUM (
    'owner',
    'admin',
    'member'
);

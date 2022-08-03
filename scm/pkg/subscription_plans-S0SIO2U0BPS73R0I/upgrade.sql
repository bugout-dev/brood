CREATE TABLE public.subscription_plans (
    id uuid NOT NULL,
    name character varying NOT NULL,
    description character varying,
    stripe_product_id character varying,
    stripe_price_id character varying,
    default_units integer,
    plan_type character varying NOT NULL,
    public boolean NOT NULL
);

ALTER TABLE ONLY public.subscription_plans
    ADD CONSTRAINT pk_subscription_plans PRIMARY KEY (id);


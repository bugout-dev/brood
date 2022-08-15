CREATE TABLE public.subscriptions (
    group_id uuid NOT NULL,
    subscription_plan_id uuid NOT NULL,
    stripe_customer_id character varying,
    stripe_subscription_id character varying,
    active boolean NOT NULL,
    units integer NOT NULL
);

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT pk_subscriptions PRIMARY KEY (group_id, subscription_plan_id);

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT fk_subscription_plans_subscription_plan_id FOREIGN KEY (subscription_plan_id) REFERENCES public.subscription_plans(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT fk_subscriptions_group_id FOREIGN KEY (group_id) REFERENCES public.groups(id) ON DELETE CASCADE;

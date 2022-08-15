CREATE TABLE public.kv_brood (
    kv_key character varying NOT NULL,
    kv_value character varying NOT NULL
);

ALTER TABLE ONLY public.kv_brood
    ADD CONSTRAINT pk_kv_brood PRIMARY KEY (kv_key);


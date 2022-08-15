stdargs @ { scm, ... }:

scm.schema {
    guid = "S0SIO2U0BPS73R0I";
    name = "subscription_plans";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-04-subscription_plans-R001COM4JVE4WXLI>
    ];
}

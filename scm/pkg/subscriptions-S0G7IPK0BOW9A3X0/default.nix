stdargs @ { scm, ... }:

scm.schema {
    guid = "S0G7IPK0BOW9A3X0";
    name = "subscriptions";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <groups-S0A0GPZRCZWRH37E>
        <subscription_plans-S0SIO2U0BPS73R0I>
        <2022-08-03-subscriptions-R001CMT8JZKHR4N5>
    ];
}

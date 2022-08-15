stdargs @ { scm, ... }:

scm.schema {
    guid = "S0G7IPK0BOW9A3X0";
    name = "subscriptions";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <subscription_plans-S0SIO2U0BPS73R0I>
        <groups-S0A0GPZRCZWRH37E>
        <2022-08-04-subscriptions-R001COM7F2DVLG0I>
    ];
}

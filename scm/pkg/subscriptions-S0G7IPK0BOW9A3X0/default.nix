stdargs @ { scm, ... }:

scm.schema {
    guid = "S0G7IPK0BOW9A3X0";
    name = "subscriptions";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-03-subscriptions-R001CMT8JZKHR4N5>
    ];
}

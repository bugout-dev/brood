stdargs @ { scm, ... }:

scm.revision {
    guid = "R001CMT7XT2NZT50";
    name = "2022-08-03-subscription_plans";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

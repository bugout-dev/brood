stdargs @ { scm, ... }:

scm.revision {
    guid = "R001COM4JVE4WXLI";
    name = "2022-08-04-subscription_plans";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

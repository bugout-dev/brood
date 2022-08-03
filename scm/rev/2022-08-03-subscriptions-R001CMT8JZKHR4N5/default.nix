stdargs @ { scm, ... }:

scm.revision {
    guid = "R001CMT8JZKHR4N5";
    name = "2022-08-03-subscriptions";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

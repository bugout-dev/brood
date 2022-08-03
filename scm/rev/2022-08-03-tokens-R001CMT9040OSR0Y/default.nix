stdargs @ { scm, ... }:

scm.revision {
    guid = "R001CMT9040OSR0Y";
    name = "2022-08-03-tokens";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

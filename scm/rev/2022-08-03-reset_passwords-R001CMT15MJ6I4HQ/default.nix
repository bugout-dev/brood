stdargs @ { scm, ... }:

scm.revision {
    guid = "R001CMT15MJ6I4HQ";
    name = "2022-08-03-reset_passwords";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

stdargs @ { scm, ... }:

scm.revision {
    guid = "R001CMT54R0WTCKP";
    name = "2022-08-03-resources";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

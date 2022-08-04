stdargs @ { scm, ... }:

scm.revision {
    guid = "R001COLWG9JG6BPL";
    name = "2022-08-04-groups";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

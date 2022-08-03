stdargs @ { scm, ... }:

scm.revision {
    guid = "R001CMSZ8NUGMH8P";
    name = "2022-08-03-groups";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

stdargs @ { scm, ... }:

scm.revision {
    guid = "R001CMT4E9EFB2E2";
    name = "2022-08-03-resource_permissions";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

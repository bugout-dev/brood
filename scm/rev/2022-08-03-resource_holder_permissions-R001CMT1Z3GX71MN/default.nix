stdargs @ { scm, ... }:

scm.revision {
    guid = "R001CMT1Z3GX71MN";
    name = "2022-08-03-resource_holder_permissions";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

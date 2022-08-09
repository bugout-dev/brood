stdargs @ { scm, ... }:

scm.revision {
    guid = "R001CXU6R8PO5M2Z";
    name = "2022-08-09-config";
    basefiles = ./basefiles;
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

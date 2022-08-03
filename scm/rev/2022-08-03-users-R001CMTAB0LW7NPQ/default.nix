stdargs @ { scm, ... }:

scm.revision {
    guid = "R001CMTAB0LW7NPQ";
    name = "2022-08-03-users";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

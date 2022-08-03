stdargs @ { scm, ... }:

scm.revision {
    guid = "R001CMSUKKWM8GDI";
    name = "2022-08-03-group_invites";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

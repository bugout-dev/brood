stdargs @ { scm, ... }:

scm.revision {
    guid = "R001CMSXKU12ES6O";
    name = "2022-08-03-group_users";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

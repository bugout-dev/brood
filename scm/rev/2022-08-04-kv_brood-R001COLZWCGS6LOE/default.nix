stdargs @ { scm, ... }:

scm.revision {
    guid = "R001COLZWCGS6LOE";
    name = "2022-08-04-kv_brood";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

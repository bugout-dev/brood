stdargs @ { scm, ... }:

scm.revision {
    guid = "R001CMT09GIWDEA4";
    name = "2022-08-03-kv_brood";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

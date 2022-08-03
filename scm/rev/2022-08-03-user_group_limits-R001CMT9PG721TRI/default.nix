stdargs @ { scm, ... }:

scm.revision {
    guid = "R001CMT9PG721TRI";
    name = "2022-08-03-user_group_limits";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

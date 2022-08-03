stdargs @ { scm, ... }:

scm.schema {
    guid = "S0F2W3B8BMBB6URM";
    name = "user_group_limits";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-03-user_group_limits-R001CMT9PG721TRI>
    ];
}

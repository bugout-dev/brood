stdargs @ { scm, ... }:

scm.revision {
    guid = "R001COM8ME1STTAA";
    name = "2022-08-04-user_group_limits";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-04-users-R001COLV3XMNUS2V>
    ];
}

stdargs @ { scm, ... }:

scm.revision {
    guid = "R001COLYVOS4QTRR";
    name = "2022-08-04-group_invites";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-04-users-R001COLV3XMNUS2V>
        <2022-08-04-groups-R001COLWG9JG6BPL>
    ];
}

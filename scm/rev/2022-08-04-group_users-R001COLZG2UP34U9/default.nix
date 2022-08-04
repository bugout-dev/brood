stdargs @ { scm, ... }:

scm.revision {
    guid = "R001COLZG2UP34U9";
    name = "2022-08-04-group_users";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-04-users-R001COLV3XMNUS2V>
        <2022-08-04-groups-R001COLWG9JG6BPL>
    ];
}

stdargs @ { scm, ... }:

scm.revision {
    guid = "R001COM42RUIPBMW";
    name = "2022-08-04-resource_holder_permissions";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-04-users-R001COLV3XMNUS2V>
        <2022-08-04-resources-R001COM0WJ7NLLA5>
        <2022-08-04-resource_permissions-R001COM1AP03N1JK>
        <2022-08-04-groups-R001COLWG9JG6BPL>
    ];
}

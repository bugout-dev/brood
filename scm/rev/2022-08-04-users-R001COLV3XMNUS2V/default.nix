stdargs @ { scm, ... }:

scm.revision {
    guid = "R001COLV3XMNUS2V";
    name = "2022-08-04-users";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-04-applications-R001COLRG3TB6US5>
    ];
}

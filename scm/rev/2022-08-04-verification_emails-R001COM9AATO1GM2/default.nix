stdargs @ { scm, ... }:

scm.revision {
    guid = "R001COM9AATO1GM2";
    name = "2022-08-04-verification_emails";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-04-users-R001COLV3XMNUS2V>
    ];
}

stdargs @ { scm, ... }:

scm.revision {
    guid = "R001COM08U6G5TM8";
    name = "2022-08-04-reset_passwords";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-04-users-R001COLV3XMNUS2V>
    ];
}

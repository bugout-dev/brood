stdargs @ { scm, ... }:

scm.schema {
    guid = "S0L9PZDL6NX8I1U8";
    name = "verification_emails";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <users-S0382XBF5ZCEJG69>
        <2022-08-04-verification_emails-R001COM9AATO1GM2>
    ];
}

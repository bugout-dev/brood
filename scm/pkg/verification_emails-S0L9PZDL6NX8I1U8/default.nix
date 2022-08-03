stdargs @ { scm, ... }:

scm.schema {
    guid = "S0L9PZDL6NX8I1U8";
    name = "verification_emails";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-03-verification_emails-R001CMTAVBH7MJ6N>
    ];
}

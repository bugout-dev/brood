stdargs @ { scm, ... }:

scm.schema {
    guid = "S0L3BK1JD0M0SAHU";
    name = "resource_permissions";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-03-resource_permissions-R001CMT4E9EFB2E2>
    ];
}

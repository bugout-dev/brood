stdargs @ { scm, ... }:

scm.schema {
    guid = "S0L3BK1JD0M0SAHU";
    name = "resource_permissions";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <resources-S0EWRO2U5R3QRV2G>
        <2022-08-04-resource_permissions-R001COM1AP03N1JK>
    ];
}

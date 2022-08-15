stdargs @ { scm, ... }:

scm.schema {
    guid = "S0EWRO2U5R3QRV2G";
    name = "resources";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <applications-S0TI8JF1EIYWHAPA>
        <2022-08-04-resources-R001COM0WJ7NLLA5>
    ];
}

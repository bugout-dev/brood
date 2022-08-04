stdargs @ { scm, ... }:

scm.schema {
    guid = "S0EWRO2U5R3QRV2G";
    name = "resources";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <applications-S0TI8JF1EIYWHAPA>
        <2022-08-03-resources-R001CMT54R0WTCKP>
    ];
}

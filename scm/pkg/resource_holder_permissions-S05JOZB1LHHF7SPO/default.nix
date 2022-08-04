stdargs @ { scm, ... }:

scm.schema {
    guid = "S05JOZB1LHHF7SPO";
    name = "resource_holder_permissions";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <groups-S0A0GPZRCZWRH37E>
        <resource_permissions-S0L3BK1JD0M0SAHU>
        <resources-S0EWRO2U5R3QRV2G>
        <users-S0382XBF5ZCEJG69>
        <2022-08-03-resource_holder_permissions-R001CMT1Z3GX71MN>
    ];
}

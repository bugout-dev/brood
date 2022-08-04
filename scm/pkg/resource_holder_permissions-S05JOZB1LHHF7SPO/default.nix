stdargs @ { scm, ... }:

scm.schema {
    guid = "S05JOZB1LHHF7SPO";
    name = "resource_holder_permissions";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <users-S0382XBF5ZCEJG69>
        <resources-S0EWRO2U5R3QRV2G>
        <resource_permissions-S0L3BK1JD0M0SAHU>
        <groups-S0A0GPZRCZWRH37E>
        <2022-08-04-resource_holder_permissions-R001COM42RUIPBMW>
    ];
}

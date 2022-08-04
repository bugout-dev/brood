stdargs @ { scm, ... }:

scm.schema {
    guid = "S00PPBEMYZ1PKTEZ";
    name = "group_invites";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <users-S0382XBF5ZCEJG69>
        <groups-S0A0GPZRCZWRH37E>
        <2022-08-03-group_invites-R001CMSUKKWM8GDI>
    ];
}

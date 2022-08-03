stdargs @ { scm, ... }:

scm.schema {
    guid = "S00PPBEMYZ1PKTEZ";
    name = "group_invites";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-03-group_invites-R001CMSUKKWM8GDI>
    ];
}

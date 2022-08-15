stdargs @ { scm, ... }:

scm.revision {
    guid = "R001COM7F2DVLG0I";
    name = "2022-08-04-subscriptions";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-04-subscription_plans-R001COM4JVE4WXLI>
        <2022-08-04-groups-R001COLWG9JG6BPL>
    ];
}

stdargs @ { scm, ... }:

scm.schema {
    guid = "S0382XBF5ZCEJG69";
    name = "users";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <applications-S0TI8JF1EIYWHAPA>
        <2022-08-03-users-R001CMTAB0LW7NPQ>
    ];
}

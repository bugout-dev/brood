stdargs @ { scm, ... }:

scm.schema {
    guid = "S0382XBF5ZCEJG69";
    name = "users";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-03-users-R001CMTAB0LW7NPQ>
    ];
}

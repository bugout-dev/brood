stdargs @ { scm, ... }:

scm.schema {
    guid = "S0F2W3B8BMBB6URM";
    name = "user_group_limits";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <users-S0382XBF5ZCEJG69>
        <2022-08-04-user_group_limits-R001COM8ME1STTAA>
    ];
}

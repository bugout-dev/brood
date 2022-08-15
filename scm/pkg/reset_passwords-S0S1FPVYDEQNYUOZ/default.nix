stdargs @ { scm, ... }:

scm.schema {
    guid = "S0S1FPVYDEQNYUOZ";
    name = "reset_passwords";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <users-S0382XBF5ZCEJG69>
        <2022-08-04-reset_passwords-R001COM08U6G5TM8>
    ];
}

stdargs @ { scm, ... }:

scm.schema {
    guid = "S0ZU2G5A18O17PAL";
    name = "tokens";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <users-S0382XBF5ZCEJG69>
        <2022-08-04-tokens-R001COM7V7TCFQA9>
    ];
}

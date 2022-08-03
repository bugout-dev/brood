stdargs @ { scm, ... }:

scm.schema {
    guid = "S0NMJU4T9AUYSUBI";
    name = "group_users";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-03-group_users-R001CMSXKU12ES6O>
    ];
}

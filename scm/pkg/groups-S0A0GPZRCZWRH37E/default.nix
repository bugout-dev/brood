stdargs @ { scm, ... }:

scm.schema {
    guid = "S0A0GPZRCZWRH37E";
    name = "groups";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-03-groups-R001CMSZ8NUGMH8P>
    ];
}

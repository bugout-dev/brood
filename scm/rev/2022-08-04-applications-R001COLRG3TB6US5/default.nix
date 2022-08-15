stdargs @ { scm, ... }:

scm.revision {
    guid = "R001COLRG3TB6US5";
    name = "2022-08-04-applications";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-04-groups-R001COLWG9JG6BPL>
    ];
}

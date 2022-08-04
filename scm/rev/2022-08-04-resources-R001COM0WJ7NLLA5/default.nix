stdargs @ { scm, ... }:

scm.revision {
    guid = "R001COM0WJ7NLLA5";
    name = "2022-08-04-resources";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-04-applications-R001COLRG3TB6US5>
    ];
}

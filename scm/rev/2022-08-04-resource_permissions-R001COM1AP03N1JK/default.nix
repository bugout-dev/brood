stdargs @ { scm, ... }:

scm.revision {
    guid = "R001COM1AP03N1JK";
    name = "2022-08-04-resource_permissions";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-04-resources-R001COM0WJ7NLLA5>
    ];
}

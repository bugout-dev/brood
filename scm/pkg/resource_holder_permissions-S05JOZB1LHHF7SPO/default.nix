stdargs @ { scm, ... }:

scm.schema {
    guid = "S05JOZB1LHHF7SPO";
    name = "resource_holder_permissions";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-03-resource_holder_permissions-R001CMT1Z3GX71MN>
    ];
}

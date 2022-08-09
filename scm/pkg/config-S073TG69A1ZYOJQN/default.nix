stdargs @ { scm, ... }:

scm.schema {
    guid = "S073TG69A1ZYOJQN";
    name = "config";
    upgrade_sql = ./upgrade.sql;
    basefiles = ./basefiles;
    dependencies = [
        <2022-08-09-config-R001CXU6R8PO5M2Z>
    ];
}


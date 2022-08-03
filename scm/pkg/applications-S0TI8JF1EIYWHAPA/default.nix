stdargs @ { scm, ... }:

scm.schema {
    guid = "S0TI8JF1EIYWHAPA";
    name = "applications";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-03-applications-R001CMRUT2UHVZML>
    ];
}

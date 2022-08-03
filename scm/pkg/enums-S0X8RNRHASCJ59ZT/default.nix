stdargs @ { scm, ... }:

scm.schema {
    guid = "S0X8RNRHASCJ59ZT";
    name = "enums";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-03-enums-R001CMSOUYN49CGS>
    ];
}

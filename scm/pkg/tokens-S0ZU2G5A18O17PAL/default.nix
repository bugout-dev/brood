stdargs @ { scm, ... }:

scm.schema {
    guid = "S0ZU2G5A18O17PAL";
    name = "tokens";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-03-tokens-R001CMT9040OSR0Y>
    ];
}

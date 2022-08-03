stdargs @ { scm, ... }:

scm.schema {
    guid = "S0S1FPVYDEQNYUOZ";
    name = "reset_passwords";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-03-reset_passwords-R001CMT15MJ6I4HQ>
    ];
}

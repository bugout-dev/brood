stdargs @ { scm, ... }:

scm.schema {
    guid = "S0BHBK9VM7PFLJZD";
    name = "kv_brood";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-04-kv_brood-R001COLZWCGS6LOE>
    ];
}

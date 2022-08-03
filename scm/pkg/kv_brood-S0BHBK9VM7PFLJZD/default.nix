stdargs @ { scm, ... }:

scm.schema {
    guid = "S0BHBK9VM7PFLJZD";
    name = "kv_brood";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        <2022-08-03-kv_brood-R001CMT09GIWDEA4>
    ];
}

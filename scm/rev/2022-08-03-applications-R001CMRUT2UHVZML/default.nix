stdargs @ { scm, ... }:

scm.revision {
    guid = "R001CMRUT2UHVZML";
    name = "2022-08-03-applications";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

stdargs @ { scm, ... }:

scm.revision {
    guid = "R001CMTAVBH7MJ6N";
    name = "2022-08-03-verification_emails";
    upgrade_sql = ./upgrade.sql;
    dependencies = [
        
    ];
}

use role accountadmin;
CREATE OR REPLACE WAREHOUSE HOL_WH WAREHOUSE_SIZE = XSMALL, AUTO_SUSPEND = 300, AUTO_RESUME= TRUE;

use role securityadmin;
create or replace role hol_role;
grant role hol_role to role sysadmin;
GRANT OWNERSHIP ON WAREHOUSE HOL_WH to ROLE HOL_ROLE;

use role useradmin;
create or replace user hol_user
default_warehouse = HOL_WH
default_role = HOL_ROLE
rsa_public_key="MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAtWYefr7DR1DyLS7er1xR
2PwkqLJe/7ILZEoiwxKYulyz3QNdhcKn/joZ0IDmYKG0pxqzP9O76Yqpacupy77M
C0lprjGQe4JRL//cBdcC4J6fKx7WFbtgGEkXxptoYpubwmXWf2TZE+COL7pO6PDq
mY55Vjg6T7vMKmVTwiNmy3w6Yxx8dKk9q4OitcWQKtM9bz/ACM1M1M7hIg0Ezai4
2kAkCsTm8PN6Yt+wipUzeXvSLmxI/O7jUfnAKUQDgwYCElzswVejv7KkGp7CR5Kg
MjgubX011MUoRSA0Mbv4VBhQ4Mr1PkUksE3hKP++0I4/yOTPYH4yuolaN56Z8Miz
swIDAQAB";

CREATE STORAGE INTEGRATION azure_integration
TYPE = EXTERNAL_STAGE
STORAGE_PROVIDER = 'AZURE'
ENABLED = TRUE
AZURE_TENANT_ID = '*** PUT TENANT ID HERE AS PART OF DEMO SETUP ***'
STORAGE_ALLOWED_LOCATIONS = ('azure://sfpro.blob.core.windows.net/sfpro-container/sfprod_stage',
'azure://sfpro.blob.core.windows.net/sfpro-container/snowpark_hol_stage');

use role securityadmin;
grant usage on storage integration azure_integration to role hol_role;
grant role hol_role to user hol_user;

use role accountadmin;
grant execute task on account to role hol_role;
grant monitor execution on account to role hol_role;

use role securityadmin;
grant imported privileges on database snowflake to role hol_role;

use role sysadmin;
CREATE OR REPLACE DATABASE HOL_DB;

use role securityadmin;
GRANT OWNERSHIP ON DATABASE HOL_DB to ROLE HOL_ROLE;

use role useradmin;
alter user hol_user set default_database = HOL_DB;
alter user hol_user set default_role = hol_role;

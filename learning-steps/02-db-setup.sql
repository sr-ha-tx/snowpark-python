USE ROLE HOL_ROLE;
USE WAREHOUSE HOL_WH;
USE DATABASE HOL_DB;

-- Schemas
CREATE OR REPLACE SCHEMA EXTERNAL;
CREATE OR REPLACE SCHEMA RAW_POS;
CREATE OR REPLACE SCHEMA RAW_CUSTOMER;
CREATE OR REPLACE SCHEMA HARMONIZED;
CREATE OR REPLACE SCHEMA ANALYTICS;

-- External Frostbyte objects
USE SCHEMA EXTERNAL;
CREATE OR REPLACE FILE FORMAT PARQUET_FORMAT
    TYPE = PARQUET
    COMPRESSION = SNAPPY
;
CREATE OR REPLACE STAGE FROSTBYTE_RAW_STAGE
    STORAGE_INTEGRATION = azure_integration
    --URL = 's3://sfquickstarts/data-engineering-with-snowpark-python/'
    URL = 'azure://sfpro.blob.core.windows.net/sfpro-container/snowpark_hol_stage';



// Next we are using Snowflake CLI to create teh procedures aand functions required for the demo.
// Use the code inside my_sprocs directory to create the procedures and functions using below 

// 1. `snow snowpark build`

// 2. `snow snowpark deploy --database <DB> --schema <SCHEMA>`

// Once the procedures and function are created, we can use below to execute

use database hol_db;
use role hol_role;
use schema external;
call load_excel_spreadsheet_to_table(BUILD_SCOPED_FILE_URL(@FROSTBYTE_RAW_STAGE, 'intro/order_detail.xlsx'), 'order_detail', 'ORDER_DETAIL');
call load_excel_spreadsheet_to_table(BUILD_SCOPED_FILE_URL(@FROSTBYTE_RAW_STAGE, 'intro/location.xlsx'), 'location', 'location');

describe table location;
select 'LOCATION' as table_name, count(*) as row_count from location;
describe table order_detail;
select 'ORDER_DETAIL' as table_name, count(*) as row_count from order_detail;

-- Execute LOAD DAILY CITY METRICS stored procedure
call load_daily_city_metrics_gisp('EXTERNAL', 'DAILY_CITY_METRICS');



list @S3_FROSTBYTE_RAW_STAGE;

-- CREATE OR REPLACE STAGE S3_FROSTBYTE_RAW_STAGE
--     URL = 's3://sfquickstarts/data-engineering-with-snowpark-python/';
--     -- URL = 'azure://sfpro.blob.core.windows.net/sfpro-container/snowpark-hol-stage';


-- desc stage FROSTBYTE_RAW_STAGE;

-- -- ANALYTICS objects
-- USE SCHEMA ANALYTICS;
-- -- This will be added in step 5
-- CREATE OR REPLACE FUNCTION ANALYTICS.FAHRENHEIT_TO_CELSIUS_UDF(TEMP_F NUMBER(35,4))
-- RETURNS NUMBER(35,4)
-- AS
-- $$
--    (temp_f - 32) * (5/9)
-- $$;

-- CREATE OR REPLACE FUNCTION ANALYTICS.INCH_TO_MILLIMETER_UDF(INCH NUMBER(35,4))
-- RETURNS NUMBER(35,4)
--     AS
-- $$
--     inch * 25.4
-- $$;

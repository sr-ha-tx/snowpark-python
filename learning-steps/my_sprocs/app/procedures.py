from __future__ import annotations

import sys

from common import print_hello
from snowflake.snowpark import Session
from snowflake.snowpark.files import SnowflakeFile
import snowflake.snowpark.functions as F
from openpyxl import load_workbook
import pandas as pd
from logging import getLogger, StreamHandler, INFO

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
logger.addHandler(handler)

# POS_TABLES = ['country', 'franchise', 'location', 'menu', 'truck', 'order_header', 'order_detail']
POS_TABLES = [ 'truck' ]
# CUSTOMER_TABLES = ['customer_loyalty']
CUSTOMER_TABLES = []
TABLE_DICT = {
    "pos": {"schema": "RAW_POS", "tables": POS_TABLES},
    "customer": {"schema": "RAW_CUSTOMER", "tables": CUSTOMER_TABLES}
}

def load_parquet_to_table(session: Session, s3dir, tabname, schema, year=None):
    logger.info(f"Beginning Load to {tabname} from {s3dir}/{tabname}/{year}")
    if year:
        location = f'@s3_frostbyte_raw_stage/{s3dir}/{tabname}/year={year}'
    else:
        location = f'@s3_frostbyte_raw_stage/{s3dir}/{tabname}'
    
    session = Session.builder.getOrCreate()
    # session.use_schema(schema)
    df = session.read.option('compression', 'snappy').parquet(location)
    df.copy_into_table(['HOL_DB', schema, tabname])
    return f"Loaded {location} into table {schema}.{tabname}"

def load_all_raw_tables(session: Session):
    ret_str = []
    for s3dir, data in TABLE_DICT.items():
        schema = data['schema']
        tables = data['tables']
        for table in tables:
            if table in ['order_Detail', 'order_header']:
                for year in  ['2021']:
                    ret = load_parquet_to_table(session, s3dir, table, schema, year)
            else:
                ret = load_parquet_to_table(session, s3dir, table, schema)
            ret_str.append(ret)
    return ret_str




def hello_procedure(session: Session, name: str) -> str:
    return print_hello(name)


def test_procedure(session: Session) -> str:
    return "Test procedure"

def load_excel_spreadsheet_to_table(session: Session, file_path :str, worksheet_name : str, target_table :str):
    with SnowflakeFile.open(file_path, 'rb') as f:
        workbook = load_workbook(f)
        sheet = workbook.get_sheet_by_name(worksheet_name)
        data =  sheet.values

        columns = next(data)
        df = pd.DataFrame(data, columns= columns)

        with Session.builder.getOrCreate() as session:
            df2 = session.create_dataframe(df)
            df2.write.mode("overwrite").save_as_table(target_table)
    return f"Data loaded to {target_table} from {file_path}"

def table_exists(schema ='', name=''):
    with Session.builder.getOrCreate() as session:
        exists = session.sql(f"SELECT EXISTS (SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{name}') as TABLE_EXISTS").collect()[0]['TABLE_EXISTS']
    return exists

def load_daily_city_metrics_sp(session: Session, schema_name: str, table_name: str):
    with Session.builder.getOrCreate() as session:
        order_detail = session.table("HOL_DB.EXTERNAL.ORDER_DETAIL")
        history_day = session.table("FROSTBYTE_WEATHERSOURCE.ONPOINT_ID.HISTORY_DAY")
        location = session.table("HOL_DB.EXTERNAL.LOCATION")

        # Join the tables
        order_detail = order_detail.join(location, order_detail['LOCATION_ID'] == location['LOCATION_ID'], rsuffix='_l')
        order_detail = order_detail.join(history_day, (F.builtin("DATE")(order_detail['ORDER_TS']) == history_day['DATE_VALID_STD']) & (location['ISO_COUNTRY_CODE'] == history_day['COUNTRY']) & (location['CITY'] == history_day['CITY_NAME']), rsuffix='_h')
        
        final_agg = order_detail.group_by( F.col('DATE_VALID_STD'), F.col('CITY_NAME'), F.col('ISO_COUNTRY_CODE')) \
                            .agg( \
                                F.sum('PRICE').alias('TOTAL_SALES_SUM'), \
                                F.avg('AVG_TEMPERATURE_AIR_2M_F').alias('AVG_TEMPERATURE_F'), \
                                F.avg('TOT_PRECIPITATION_IN').alias('AVG_PRECIPITATION_IN'), \
                            ) \
                            .select( \
                                F.col('DATE_VALID_STD').alias('DATE'), \
                                F.col('CITY_NAME'), \
                                F.col('ISO_COUNTRY_CODE').alias('COUNTRY_DESC'), \
                                F.builtin('ZEROIFNULL')(F.col('TOTAL_SALES_SUM')).alias('DAILY_SALES'), \
                                F.round(F.col('AVG_TEMPERATURE_F'), 2).alias('AVG_TEMPERATURE_FAHRENHEIT'), \
                                F.round(F.col('AVG_PRECIPITATION_IN'), 2).alias('AVG_PRECIPITATION_INCHES'), \
                                )
        
        
        if not table_exists(schema_name, table_name):
            final_agg.write.mode("overwrite").save_as_table(f"{schema_name}.{table_name}")
            return f"Successfully loaded aggregate data to {schema_name}.{table_name}"
        else:
            cols_to_update = {c: final_agg[c] for c in final_agg.schema.names}
            dcm = session.table(f"{schema_name}.{table_name}")
            dcm.merge(final_agg, (dcm['DATE'] == final_agg['DATE']) & (dcm['CITY_NAME'] == final_agg['CITY_NAME']) & (dcm['COUNTRY_DESC'] == final_agg['COUNTRY_DESC']), \
                      [F.when_matched().update(cols_to_update), F.when_not_matched().insert(cols_to_update)])


# For local debugging
# Beware you may need to type-convert arguments if you add input parameters
if __name__ == "__main__":
    # Create a local Snowpark session
    with Session.builder.config("connection_name", 'HOL').getOrCreate() as session:
        load_all_raw_tables(session)
        # load_parquet_to_table(session, 'pos', 'order_header', 'raw_pos', '2021')
        # print(hello_procedure(session, *sys.argv[1:]))  # type: ignore

import pandas as pd

from os import getenv
from sqlalchemy import create_engine


def ergodex_analytics(df, ergo):

    # JOIN LP QUANTITY WITH PRICING DATA
    df_final = df.merge(ergo, how='left', on='date')

    # SET STATIC VARIABLES FOR INITIAL INVESTMENT
    ilp1 = df_final.lp_pair1[0]
    ilp2 = df_final.lp_pair2[0]
    ilp_ratio = ilp1 / ilp2
    ilp_price = df_final.price[0]

    # CALCULATE PERFORMANCE ANALYTICS
    df_final['ratio'] = df_final.lp_pair1 / df_final.lp_pair2
    df_final['lp_value1'] = df_final.lp_pair1 * df_final.price
    df_final['lp_value2'] = df_final.lp_pair2 * df_final.price * df_final.ratio
    df_final['lp_investment'] = df_final.lp_value1 + df_final.lp_value2
    df_final['hodl_instead'] = (ilp1 * df_final.price) + (ilp2 * df_final.price * ilp_ratio)
    df_final['erg_diff'] = 100 * (df_final.price / ilp_price - 1)
    df_final['lp_vs_hodl'] = 100 * (df_final.lp_investment / df_final.hodl_instead - 1)

    return(df_final)

### MAIN
if __name__ == '__main__':
    # daily price data for ergo
    src = f"postgresql://{getenv('POSTGRES_USER')}:{getenv('POSTGRES_PASSWORD')}@{getenv('POSTGRES_HOST')}:{getenv('POSTGRES_PORT')}/hello",
    con = create_engine(src)
    ergo = pd.read_sql_table('select * from "coinex_ERG/USDT_1d"', con=con)

    # liquidity pairs
    ergodex_data_raw = "/path/to/file/ergodex-data.csv"
    ergodex_data = pd.read_csv(ergodex_data_raw)
    ergodex_data['date'] = pd.to_datetime(ergodex_data['date'])

    # final dataset
    df_lp = ergodex_analytics(ergodex_data, ergo)
    df_lp = df_lp.iloc[1:]

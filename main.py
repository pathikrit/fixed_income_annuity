from datetime import date, datetime
from dateutil.relativedelta import relativedelta

import pandas as pd
import streamlit as st

#### This is the input to this program ####

TARGET_MONTHLY_CASHFLOW_BY_YEAR = [(year, 48000 - (2039 - year) * 1000 if year < 2040 else 51000 - (2048 - year) * 1000) for year in range(2025, 2049)]
FIDELITY_FIXED_INCOME_SEARCH_RESULTS = ['~/Downloads/Fidelity_FixedIncome_SearchResults.csv']
PAYOUT_MONTHS = 12 # at most 1 lump sum payment in this many months

###########################################

plan = pd.DataFrame(data=TARGET_MONTHLY_CASHFLOW_BY_YEAR, columns=['year', 'target_monthly_cashflow'])
plan['target_cashflow'] = plan['target_monthly_cashflow'] * 12
plan['cashflow'] = 0
plan.set_index('year')

def buy(security, qty):
    cusip = security['cusip']
    plan[f'cashflow_{cusip}'] = plan.apply(lambda row: 0 if row['year'] > security['maturity_date'].year else ((row['year'] == security['maturity_date'].year) + security['rate']) * security['redemption'] * qty, axis=1)
    plan['cashflow'] += plan[f'cashflow_{security.cusip}']
    securities.loc[securities['cusip'] == cusip, 'buy'] = qty

securities = pd.concat([pd.read_csv(file) for file in FIDELITY_FIXED_INCOME_SEARCH_RESULTS])
securities['cusip'] = securities['Cusip'].str.replace('="', '').str.replace('"', '')
securities.set_index('cusip')
securities['rate'] = securities['Coupon'] / 100
securities['price'] = securities['Price Ask']
securities['redemption'] = 100
securities['yield'] = securities['Ask Yield to Worst']
securities['maturity_date'] = pd.to_datetime(securities['Maturity Date'], format='%m/%d/%Y')
securities['buy'] = 0
securities = securities.dropna(subset=['rate'])

def find_best(end_date: date):
    t = datetime.combine(end_date, datetime.max.time()) # TODO: remove this - we should just use date columns for maturity_date
    investable = securities[(securities['maturity_date'] <= t) & (securities['maturity_date'] >= t - relativedelta(months=PAYOUT_MONTHS))]
    return investable[investable['yield'] == investable['yield'].max()].sort_values(by=['maturity_date']).iloc[0]

temp = find_best(date(2048, 12, 31))
buy(temp, qty=10)

class STREAMLIT_FORMATS(object):
    CURRENCY = '$%.0f'
    PERCENT = '%.2f%%'
    NUMBER = '%d'

st.dataframe(
    data=securities[['cusip', 'Coupon', 'price', 'Ask Yield to Worst', 'maturity_date', 'buy']].sort_values(by=['buy', 'maturity_date']),
    column_config={
        'cusip': st.column_config.TextColumn(label='CUSIP'),
        'Coupon': st.column_config.NumberColumn(format=STREAMLIT_FORMATS.PERCENT),
        'maturity_date': st.column_config.DateColumn(label='Maturity', format='YYYY-MM-DD'),
        'price': st.column_config.NumberColumn(label='Price', format=STREAMLIT_FORMATS.CURRENCY),
        'yield': st.column_config.NumberColumn(label='Yield', format=STREAMLIT_FORMATS.PERCENT),
        'buy': st.column_config.NumberColumn(label='Buy', format=STREAMLIT_FORMATS.NUMBER),
    }
)

st.dataframe(
    data=plan,
    column_config={col: st.column_config.NumberColumn(format=STREAMLIT_FORMATS.CURRENCY if 'cashflow' in col else STREAMLIT_FORMATS.NUMBER) for col in plan.columns}
)

### TODO
# 1. Print total amount needed to buy using st.metric
# 2. Unit tests
####

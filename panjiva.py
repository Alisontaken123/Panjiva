import pandas as pd
import numpy as np
import os
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")


def transform_month(month):
    dt = datetime.strptime(month, '%Y-%m')
    return dt.strftime("%B") + ' ' + dt.strftime("%Y") 

def fill_missing_intervals(df, interval):
    """fill in missing months/years
    e.g. 
    year value
    2011  1
    2013  2
    2015  5
    
    after: 
    year value
    2011    1
    2012    0
    2013    2
    2014    0
    2015    5
    """
    df[interval] = pd.to_datetime(df[interval])
    df = df.set_index(interval).sort_index()
    full_index = pd.date_range(df.index[0], df.index[-1], freq='MS')
    df = df.reindex(full_index)
    df = df.reset_index().rename(columns={'index': interval})
    return df

def add_percentage(df, col_value, col_percentage):
    """add a percentage column with respective to col_value
    """
    df[col_percentage] = df[col_value] / df[col_value].sum()
    df[col_percentage] = df[col_percentage]*100
    df[col_percentage] = df[col_percentage].round(2)
    df[col_percentage] = df[col_percentage].astype('str')
    df[col_percentage] = df[col_percentage] + '%'
    return df

def show_sorted_top_n(df, col, n):
    """only keep top-n records in the table and assign all others to 'others', and add a total row.
    """
    top_df = df[:n]
    total_value = df[col].sum()
    others_value = total_value - top_df[col].sum()
    others_percentage = str((others_value / total_value * 100).round(2)) + '%'
    df_to_append = pd.DataFrame(
            [['Others', others_value, others_percentage], ['Total', total_value, '100%']], 
            columns=df.columns)
    
    top_df = top_df.append(df_to_append)
    top_df[col] = top_df[col].astype('int')
    return top_df

def show_sorted_top_n_extra(df, col, n):
    """only keep top-n records in the table and assign all others to 'others', and add a total row.
    """
    top_df = df[:n]
    total_value = df[col].sum()
    others_value = total_value - top_df[col].sum()
    others_percentage = str((others_value / total_value * 100).round(2)) + '%'
    df_to_append = pd.DataFrame(
            [['Others', 'Others', others_value, others_percentage], 
            ['Total', 'Total', total_value, '100%']], 
            columns=df.columns)
    
    top_df = top_df.append(df_to_append)
    top_df[col] = top_df[col].astype('int')
    return top_df

def exports_summary_sentences(china_exports):
    """print summary sentences
    """
    min_month = transform_month(china_exports['month'].min())
    max_month = transform_month(china_exports['month'].max())
    value_m = china_exports['Value of Goods (USD)'].sum()/ 1e6
    value_m = str(round(value_m, 2))
    number_of_countries = len(china_exports['Country of Sale'].unique())
    number_of_hs = len(china_exports['HS Code'].unique())

    text1 = 'The china exports for the last 5 years (2013 - 2017) showed that '
    text2 = 'the products were exported to ' + str(number_of_countries) + ' regions'
    text3 = ', under ' + str(number_of_hs) + ' HS codes (2-digit) '
    text4 = 'and valued at ' + str(value_m) + ' million USD.'
    return text1 + text2 + text3 + text4

def shipment_destinations(china_exports):
    """show top n, e.g. 
    shipment destination, Value of Goods(USD), Percentage of Sale
    United States, 808080, 60.00%
    ...
    Others, 80, 20.00%
    Total, 10000000, 100%
    """
    shipment_destinations = china_exports.groupby(['Shipment Destination']).agg(
        {"Value of Goods (USD)": np.sum}).reset_index().sort_values(
        by=['Value of Goods (USD)'], ascending=False)

    shipment_destinations = add_percentage(shipment_destinations,
                            'Value of Goods (USD)', 'Percentage of Sale')

    shipment_destinations = show_sorted_top_n(shipment_destinations, 
        'Value of Goods (USD)', 10)

    shipment_destinations['Value of Goods (USD)'] = shipment_destinations['Value of Goods (USD)'].apply(lambda x: format(x,','))
    
    return shipment_destinations

def yearly_exports(china_exports):
    """yearly export values from China for the last 5 years (2018)
    """
    yearly_exports = china_exports.groupby(['year']).agg(
        {"Value of Goods (USD)": np.sum}).reset_index()
    us_exports = china_exports[china_exports['Shipment Destination'] == 'United States'].groupby(
        ['year']).agg({"Value of Goods (USD)": np.sum}).reset_index()
    yearly_exports = yearly_exports.merge(us_exports, how='left', on='year')
    yearly_exports.columns = ['year', 'Total', 'US']
    yearly_exports['year'] = yearly_exports['year'].astype('str')
    full_df = pd.DataFrame(np.zeros((5, 1)), columns=['year'])
    full_df['year'] = pd.date_range(end='2018-01-01', periods=5, freq='Y')
    full_df['year'] = full_df['year'].astype('str')
    full_df['year'] = full_df['year'].str[:4]
    yearly_exports = full_df.merge(yearly_exports, how='left', on='year')
    yearly_exports = yearly_exports.fillna(0)
    return yearly_exports

def hs_exports(china_exports):
    """summary by hs codes
    """
    hs_exports = china_exports.groupby(['HS Code','HS Code Description']).agg(
        {"Value of Goods (USD)": np.sum}).reset_index().sort_values(
    by=['Value of Goods (USD)'], ascending=False)

    hs_exports = add_percentage(hs_exports, 'Value of Goods (USD)', 
                                'Percentage of Sale')
    hs_exports = show_sorted_top_n_extra(hs_exports, 
                             'Value of Goods (USD)', 5)
    hs_exports['HS Code'] = hs_exports['HS Code'].astype('str')
    hs_exports['Value of Goods (USD)'] = hs_exports['Value of Goods (USD)'].apply(lambda x: format(x,','))
    return hs_exports

def hs_exports_summary_sentence(china_exports):
    """summary sentence for hs exports data.
    """
    hs_exports = china_exports.groupby(['HS Code','HS Code Description']).agg(
        {"Value of Goods (USD)": np.sum}).reset_index().sort_values(
    by=['Value of Goods (USD)'], ascending=False)
    number_of_hs = hs_exports.shape[0]
    text1 = 'The China export records for the last 5 years (2013 - 2017) showed that '
    text2 = 'a total of ' + str(number_of_hs) + ' of 6-digit HS Code were exported.'
    return text1 + text2

def yearly_imports_summary_sentence(us_imports):
    '''summary sentence for yearly imports data
    '''
    us_shipments = us_imports.groupby(['year']).size().reset_index(name='Number of Shipments')
    us_containers = us_imports.groupby(['year']).agg({"Number of Containers": np.sum}).reset_index()
    number_of_shipments = us_shipments['Number of Shipments'].sum() 
    number_of_containers = us_containers['Number of Containers'].sum()
    text1 = 'The US import records for the last 5 years showed that '
    text2 = str(number_of_shipments) +' shipments and ' + str(number_of_containers) + ' containers were imported to US.'
    return text1 + text2

def yearly_imports(us_imports):
    '''yearly import values to US for the last 5 years
    '''
    us_shipments = us_imports.groupby(['year']).size().reset_index(name='Number of Shipments')
    us_containers = us_imports.groupby(['year']).agg({"Number of Containers": np.sum}).reset_index()
    yearly_imports = us_shipments.merge(us_containers, how='left', on='year')
    yearly_imports['year'] = yearly_imports['year'].astype('str')
    # make an empty df
    full_df = pd.DataFrame(np.zeros((6, 1)), columns=['year'])
    full_df['year'] = pd.date_range(end=datetime.now(), periods=6, freq='YS')
    full_df['year'] = full_df['year'].astype('str')
    full_df['year'] = full_df['year'].str[:4]
    yearly_imports = full_df.merge(yearly_imports, how='left', on='year')
    yearly_imports = yearly_imports.fillna(0)
    # estimate current year full 12 months data
    modifying_ratio = 12 / datetime.now().month
    yearly_imports.loc[yearly_imports.index[-1], 'Number of Shipments'] *= modifying_ratio
    yearly_imports.loc[yearly_imports.index[-1], 'Number of Containers'] *= modifying_ratio
    yearly_imports['Number of Shipments'] = yearly_imports['Number of Shipments'].astype('int')
    yearly_imports['Number of Containers'] = yearly_imports['Number of Containers'].astype('int')

    return yearly_imports


def monthly_imports(us_imports_12):
    """monthly import values to US for the last 12 months
    """
    us_shipments_12 = us_imports_12.groupby(['month']).size().reset_index(name='Number of Shipments')
    us_containers_12 = us_imports_12.groupby(['month']).agg({"Number of Containers": np.sum}).reset_index()
    monthly_imports = us_shipments_12.merge(us_containers_12, how='left', on='month')

    full_df = pd.DataFrame(np.zeros((13,1)), columns=['month'])
    full_df['month'] = pd.date_range(end=datetime.now(), periods=13, freq='MS')
    full_df['month'] = full_df['month'].astype('str')
    full_df['month'] = full_df['month'].str[:7]
    monthly_imports = full_df.merge(monthly_imports, how='left', on='month')
    monthly_imports = monthly_imports.fillna(0)

    monthly_imports['month'] = pd.to_datetime(monthly_imports['month']).dt.strftime('%b-%y')

    return monthly_imports

def hs_imports_summary_sentence(us_imports):
    """summary setence for hs imports data
    """
    us_imports['HS Code'] = us_imports['HS Code'].astype('str')
    hs_imports = us_imports['HS Code'].str.split(';', expand=True).add_prefix('name_')
    hs_imports = pd.melt(hs_imports,  value_name = 'HS Code')
    hs_imports['HS Code'] = hs_imports['HS Code'].str.strip().str[:2]
    hs_imports = hs_imports.groupby(['HS Code']).size().reset_index(name='Number of Containers').sort_values(
        by=['Number of Containers'], ascending=False)

    number_of_hs_imports = hs_imports.shape[0]
    text1 = str(number_of_hs_imports) + ' 2-digit-HS-goods were recorded in the last 5 years. '
    text2 = 'The top goods are: '

    return text1 + text2


def hs_imports(us_imports):
    """Given us_imports dataframe, return a dataframe with HS Code, its description, # of containers and relative percentage 
    """
    us_imports['HS Code'] = us_imports['HS Code'].astype('str')
    hs_imports = us_imports['HS Code'].str.split(';', expand=True).add_prefix('name_')
    hs_imports = pd.melt(hs_imports,  value_name = 'HS Code')
    hs_imports['HS Code'] = hs_imports['HS Code'].str.strip().str[:2]
    hs_imports = hs_imports.groupby(['HS Code']).size().reset_index(name='Number of Containers').sort_values(
        by=['Number of Containers'], ascending=False)

    hs_lookup = pd.read_csv('hs_lookup.csv', low_memory=False)
    hs_lookup['HS Code'] = hs_lookup['HS Code'].astype('str')
    hs_imports = hs_imports.merge(hs_lookup, how='left',on='HS Code')
    # reorder columns
    hs_imports = hs_imports[['HS Code', 'HS Code Description', 'Number of Containers']]
    hs_imports = add_percentage(hs_imports, 
        'Number of Containers', 'Percentage (historical)')
    hs_imports = show_sorted_top_n_extra(hs_imports, 'Number of Containers', 5)

    return hs_imports

def hs_imports_merge_12(us_imports, us_imports_12):
    """Add past 12 months data in addition to historical total.
    """
    hs_imports_12 = hs_imports(us_imports_12)
    hs_imports_merge_12 = hs_imports(us_imports)
    hs_imports_merge_12 = hs_imports_merge_12.merge(hs_imports_12, how='left', on='HS Code')
    hs_imports_merge_12 = hs_imports_merge_12[['HS Code', 'HS Code Description_x', 'Number of Containers_x',
                        'Percentage (historical)_x', 'Number of Containers_y', 'Percentage (historical)_y']]
    hs_imports_merge_12.columns = ['HS Code', 'HS Code Description', 'Number of Containers (historical total)',
                                    'Percentage (historical)', 'Number of Containers (past 12 months)', 
                                    'Percentage (past 12 months)']

    for column in hs_imports_merge_12.columns:
        hs_imports_merge_12[column] = hs_imports_merge_12[column].astype(str)

    return hs_imports_merge_12

def consignees_imports_summary_sentence(us_imports):
    """summary setence for consignees.
    """
    consignees_imports = us_imports.groupby(['Consignee']).size().reset_index(name='Number of Shipments').sort_values(
    by=['Number of Shipments'], ascending=False)
    number_of_consignees = consignees_imports.shape[0]
    text = str(number_of_consignees) + ' US consignees were recorded in the last 5 years. The top customers are:'
    return text


def consignees_imports(us_imports):
    """ top 10 consignees in number of shipments
    """
    consignees_imports = us_imports.groupby(['Consignee']).size().reset_index(name='Number of Shipments').sort_values(
    by=['Number of Shipments'], ascending=False)
    consignees_imports = add_percentage(consignees_imports, 'Number of Shipments', 'Percentage of Shipments (past 5 years)')
    consignees_imports = show_sorted_top_n(consignees_imports, 'Number of Shipments', 10)

    for column in consignees_imports.columns:
        consignees_imports[column] = consignees_imports[column].astype(str)
    return consignees_imports

def consignees_imports_12_summary_sentence(us_imports_12):
    """summary sentence for consignees.
    """
    consignees_imports_12 = us_imports_12.groupby(['Consignee']).size().reset_index(name='Number of Shipments').sort_values(
    by=['Number of Shipments'], ascending=False)
    number_of_consignees = consignees_imports_12.shape[0]
    text = str(number_of_consignees) + ' US consignees were recorded in the past 12 months. The top customers are:'
    return text


def consignees_imports_12(us_imports_12):
    """ top 10 consignees in number of shipments for the past 12 months
    """
    consignees_imports_12 = us_imports_12.groupby(['Consignee']).size().reset_index(name='Number of Shipments').sort_values(
    by=['Number of Shipments'], ascending=False)
    consignees_imports_12 = add_percentage(consignees_imports_12, 'Number of Shipments', 'Percentage of Shipments (past 5 years)')
    consignees_imports_12 = show_sorted_top_n(consignees_imports_12, 'Number of Shipments', 10)

    for column in consignees_imports_12.columns:
        consignees_imports_12[column] = consignees_imports_12[column].astype(str)

    return consignees_imports_12

def recent_shipments(us_imports):
    """ list 10 most recent shipments. 
    """
    recent_shipments = us_imports[['Arrival Date', 'Shipment Destination', 'Consignee', 'Quantity', 'Weight (kg)', 'Goods Shipped']][:10]
    # take the only first line of goods shipped description
    recent_shipments['Goods Shipped'] = recent_shipments['Goods Shipped'].str.split(pat="\n").str[:1].str[0].str.capitalize()

    recent_shipments['Weight (kg)'] = recent_shipments['Weight (kg)'].astype('int')
    recent_shipments['Arrival Date'] = recent_shipments['Arrival Date'].str[5:7] + '/' + recent_shipments['Arrival Date'].str[8:10] + '/' + recent_shipments['Arrival Date'].str[:4]

    for column in recent_shipments.columns:
        recent_shipments[column] = recent_shipments[column].astype(str)
    return recent_shipments

'''
if __name__ == "__main__":
    # check files
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    for file in files:
        if file.endswith('csv') and 'China_Exports' in file:
            china_exports_file = file
        if file.endswith('csv') and 'US_Imports' in file:
            us_imports_file = file
    china_exports = pd.read_csv(china_exports_file, low_memory=False)
    us_imports = pd.read_csv(us_imports_file, low_memory=False)
    # add year column
    china_exports['year'] = pd.DatetimeIndex(china_exports['Shipment Month']).year
    us_imports['year'] = pd.DatetimeIndex(us_imports['Arrival Date']).year
    # add month column
    china_exports['month'] = china_exports['Shipment Month'].str[0:7]
    us_imports['month'] = us_imports['Arrival Date'].str[0:7]
    # make recent 12 months df of us_imports
    starting_month = str(int(str(datetime.today())[:4]) -1) + str(datetime.today())[4:7]
    us_imports_12 = us_imports[us_imports['month'] >= starting_month]
    # starts here
    print(hs_imports_merge_12(us_imports, us_imports_12))
'''
#!/usr/bin/env python

####################
# Required Modules #
####################

# Libs
import pandas as pd

#############
# Functions #
#############

def get_totals(contents):
    """
    Get unique descriptions and total qty.

    Args:
        contents (list): List of lists containing invoice details

    Returns:
        pricings (dict): Dictionary of unique descriptions and unit prices
        total_qty (dict): Dictionary of unique descriptions and total quantities
    """
    pricings = dict()
    total_qty = dict()

    for entries in contents:
        if entries[3] not in pricings:
            pricings[entries[3]] = entries[5]
            total_qty[entries[3]] = float(entries[4])
        else:
            total_qty[entries[3]] += float(entries[4])
            
    return pricings, total_qty


def extract_data(line, data_dict):
    """
    Extract data from line using for loop.

    Args:
        line (str): Line of text
        data_dict (dict): Dictionary of data

    Returns:
        str: Data extracted from line
    """
    for key in data_dict:
        if key in line:
            return data_dict[key]
    return ''


def get_data(contents):
    """
    Get data from contents.

    Args:
        contents (list): List of lists containing invoice details

    Returns:
        for_month (list): List of for_month
        do_date (list): List of do_date
        do_no (list): List of do_no
        description2 (list): List of description2
        qty (list): List of qty
    """
    for_month = list()
    do_date = list()
    do_no = list()
    description2 = list()
    qty = list()

    for sublist in contents:
        for_month.append(sublist[0])
        do_date.append(sublist[1])
        do_no.append(sublist[2])
        description2.append(sublist[3])
        qty.append(sublist[4])

    return for_month, do_date, do_no, description2, qty


def add_data(
        df_data, 
        unique_rows, 
        pricings, 
        total_qty, 
        for_month, 
        do_date, 
        do_no, 
        description2, 
        qty, 
        inv_no, 
        date, 
        sub_total, 
        subcon
):
    """
    Add data to dataframe.

    Args:
        df_data (pandas.core.frame.DataFrame): Dataframe of table
        unique_rows (int): Number of unique rows
        pricings (dict): Dictionary of unique descriptions and unit prices
        total_qty (dict): Dictionary of unique descriptions and total quantities
        for_month (list): List of for_month
        do_date (list): List of do_date
        do_no (list): List of do_no
        description2 (list): List of description2
        qty (list): List of qty
        inv_no (str): Invoice number
        date (str): Invoice date
        sub_total (float): Subtotal amount
        subcon (str): Subcon name

    Returns:
        df_data (pandas.core.frame.DataFrame): Dataframe of table
    """
    df_data.loc[0, 'Inv No.'] = inv_no
    df_data.loc[0, 'Date'] = date
    df_data.loc[0, 'Total Amt per Inv'] = sub_total

    df_data.loc[:unique_rows, 'Description'] = list(pricings.keys())
    df_data.loc[:unique_rows, 'Total Qty'] = list(total_qty.values())
    df_data.loc[:unique_rows, 'Unit Rate'] = list(pricings.values())

    df_data['For Month (YYYY MM)'] = for_month
    #df_data['Location'] = location
    df_data['Zone'] = subcon
    df_data['DO Date'] = do_date
    df_data['DO No.'] = do_no
    df_data['Description2'] = description2
    df_data['Qty'] = qty

    df_data['Total Qty'] = pd.to_numeric(df_data['Total Qty'], errors='coerce')
    df_data['Unit Rate'] = pd.to_numeric(df_data['Unit Rate'], errors='coerce')
    df_data['Total Amt per Inv'] = pd.to_numeric(df_data['Total Amt per Inv'], errors='coerce')
    df_data['Qty'] = pd.to_numeric(df_data['Qty'], errors='coerce')

    df_data['Subtotal Amount'] = df_data['Total Qty'] * df_data['Unit Rate']

    # Add units
    for i in range(len(pricings.keys())):
        if 'UNDERLOAD CHARGES' in df_data.loc[i, 'Description']:
            df_data.loc[i, 'Unit'] = 'TRIP'
        else:
            df_data.loc[i, 'Unit'] = 'm3'

    return df_data

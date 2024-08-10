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
    Get unique descriptions and total qty

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
    Extract data from line using for loop

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
    Get data from contents

    Args:
        contents (list): List of lists containing invoice details

    Returns:
        for_month (list): List of for_month
        do_date (list): List of do_date
        do_no (list): List of do_no
        description3 (list): List of description3
        qty (list): List of qty
    """
    for_month = list()
    do_date = list()
    do_no = list()
    description3 = list()
    qty = list()

    for sublist in contents:
        for_month.append(sublist[0])
        do_date.append(sublist[1])
        do_no.append(sublist[2].replace(" ", ""))  # Remove spacing between DO NO.
        description3.append(sublist[3])
        qty.append(sublist[4])

    return for_month, do_date, do_no, description3, qty


def add_data(df_data, unique_rows, pricings, total_qty, for_month, do_date, do_no, description3, qty, ref_no, date, sub_total, location, subcon):
    """
    Add data to dataframe

    Args:
        df_data (pandas.core.frame.DataFrame): Dataframe
        unique_rows (int): Number of unique rows
        pricings (dict): Dictionary of unique descriptions and unit prices
        total_qty (dict): Dictionary of unique descriptions and total quantities
        for_month (list): List of for_month
        do_date (list): List of do_date
        do_no (list): List of do_no
        description3 (list): List of description3
        qty (list): List of qty
        ref_no (str): Reference number
        date (str): Date
        sub_total (float): Sub total
        location (str): Location
        subcon (str): Subcon

    Returns:
        df_data (pandas.core.frame.DataFrame): Dataframe
    """
    df_data.loc[0, 'Ref No.'] = ref_no
    df_data.loc[0, 'Date'] = date
    df_data.loc[0, 'Total Amt per Inv'] = sub_total

    df_data.loc[:unique_rows, 'Description'] = list(pricings.keys())
    df_data.loc[:unique_rows, 'Total Qty'] = list(total_qty.values())
    df_data.loc[:unique_rows, 'Unit Price'] = list(pricings.values())

    df_data['For Month (YYYY MM)'] = for_month
    df_data['Invoice No.'] = ref_no
    df_data['Location'] = location
    df_data['For TAK or Subcon? [Pintary/BBR/KKL...etc]'] = subcon
    df_data['DO Date'] = do_date
    df_data['DO No.'] = do_no
    df_data['Description3'] = description3
    df_data['Qty'] = qty

    df_data['Ref No.'] = pd.to_numeric(df_data['Ref No.'], errors='coerce')
    df_data['Total Qty'] = pd.to_numeric(df_data['Total Qty'], errors='coerce')
    df_data['Unit Price'] = pd.to_numeric(df_data['Unit Price'], errors='coerce')
    df_data['Total Amt per Inv'] = pd.to_numeric(df_data['Total Amt per Inv'], errors='coerce')
    df_data['Invoice No.'] = pd.to_numeric(df_data['Invoice No.'], errors='coerce')
    df_data['Qty'] = pd.to_numeric(df_data['Qty'], errors='coerce')

    df_data['Subtotal Amount'] = df_data['Total Qty'] * df_data['Unit Price']

    # Add units
    for i in range(len(pricings.keys())):
        if 'UNDERLOAD CHARGES' in df_data.loc[i, 'Description']:
            df_data.loc[i, 'Unit'] = 'TRIP'
        else:
            df_data.loc[i, 'Unit'] = 'm3'

    return df_data

import pandas as pd

# Get unique descriptions and total qty
def get_totals(contents):
    pricings = dict()
    total_qty = dict()

    for entries in contents:
        if entries[3] not in pricings:
            pricings[entries[3]] = entries[5]
            total_qty[entries[3]] = float(entries[4])
        else:
            total_qty[entries[3]] += float(entries[4])
            
    return pricings, total_qty


# Extract data from line using for loop
def extract_data(line, data_dict):
    for key in data_dict:
        if key in line:
            return data_dict[key]
    return ''


# Get data from contents
def get_data(contents):
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


# Add data to dataframe
def add_data(df_data, unique_rows, pricings, total_qty, for_month, do_date, do_no, description2, qty, inv_no, date, sub_total, subcon):
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

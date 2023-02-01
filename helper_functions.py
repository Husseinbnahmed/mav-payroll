import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta, time

def transform_schedule(file_name, sheet_name):
    """ This function transforms the user input schedule into a format that can be further analyzed
    
    parameters: 
    file_name: excel or xlsx file format
    sheet_name: name of the sheet as in excel file

    returns:
    A dataframe that contains four columns, employee name, date, hour in, hour out

    """
    #read excel file
    df = pd.read_excel(file_name, sheet_name= sheet_name)

    #remove first row which usually contains the name of the building for ex. hamilton cove
    df = df.iloc[1:]

    #replace null values with a string called unknown, this will help us down the road
    df= df.replace(np.NaN, "Unknown").reset_index(drop=True).iloc[:,1:].reset_index(drop=True)

    #find the index of the first week, from here you will determine where the first week starts 
    index_of_first_week = df[df['Unnamed: 1'].str.contains("Date") == True].index[0]
    index_of_second_week = df[df['Unnamed: 1'].str.contains("Date") == True].index[1]

    #rename columns of the dataframe to match that the row of where the first week starts, the columns are now dates that start from 1/16 to 1/22 (first week only)
    df.columns = df.iloc[index_of_first_week]
    df = df.iloc[:index_of_second_week, : ]

    #lets drop any unknown value in the Date column, if there are no employees why keep it?
    #The date column is just called DATE but in reality that column contains names of each employee
    df = df[df['Date'] !="Unknown"].reset_index(drop =True)
    df = df[df['Date'] !="Name of Employee"].reset_index(drop =True)
    df = df[df['Date'] !="Date"].reset_index(drop =True)
    
    #unpivot the date while fixing the name of the employee
    melt_df = pd.melt(df, id_vars="Date")
    
    #clean up the melt dataframe by removing any employee without work hours, and remove any text like the word "day"
    melt_df = melt_df[melt_df['value'] !="Unknown"].reset_index(drop =True)
    melt_df = melt_df[melt_df['Date'] !="Day"].reset_index(drop =True)

    #some rows that contain total hours get pulled in, but we only need the time worked, our strategy to keep only hourly date was to focus on strings with the : format
    melt_df['value'] = melt_df['value'].astype("str")
    melt_df = melt_df[melt_df['value'].str.contains(":")]

    #rename some of the columns
    melt_df = melt_df.rename(columns={"Date":"Employee Name", "value":"Hours"})
    melt_df.columns.values[1] = "Date"

    #we found an interesting pattern, if the Date had an unknown string, that meant that the this is the time out, but if they had a time instead, that meant time in. 
    # so we split the data into test_df1 and test_df2 that we could then merge
    df1 = melt_df[melt_df['Date'] != "Unknown"].reset_index(drop=True)
    df1 = df1.rename(columns={"Hours":"Time In"})
    
    df2 = melt_df[melt_df['Date'] == "Unknown"].reset_index(drop=True)
    df2 = df2.rename(columns={"Hours":"Time Out"})
    df2 = df2[["Time Out"]]
    
    merged_df = pd.merge(left=df1, right=df2, left_index=True, right_index=True)

    return merged_df


def hours_worked(merged_test_df):
    """Calculates the number of hours worked by each employee in the schedule
    parameters:
    merged_test_df: a transformed dataframe

    returns:
    an additional column that computes the hours worked of each employee
    """


    #make sure that time in and out are in datetime formats
    merged_test_df['Time In'] = pd.to_datetime(merged_test_df['Time In'], format='%H:%M:%S')
    merged_test_df['Time Out'] = pd.to_datetime(merged_test_df['Time Out'], format='%H:%M:%S')

    #calculate the number of hours worked between time in and time out
    merged_test_df['Hours Worked'] = merged_test_df['Time Out'] - merged_test_df['Time In']
    merged_test_df['Hours Worked'] = merged_test_df['Hours Worked'].apply(lambda x: x.total_seconds() / 3600 if x.total_seconds() > 0 else (x + pd.Timedelta('1D')).total_seconds() / 3600)
    return merged_test_df


def get_building_name(file_name, sheet_name):
    """ Uses Regex to extract the name of the building"""
    df = pd.read_excel(file_name, sheet_name= sheet_name)
    text = df.iloc[:1]['Unnamed: 1'][0]
    
    match = re.search(r'^([\w\s]+)\s(Weekly|employees)', text, re.IGNORECASE)
    if match:
        x = match.group(1)
    else:
        x = None

    return x



def process_hours(df):
    """
    Takes a dataframe and categorizes the total hours by each employee into three categories (holliday, regular and overtime hours)

    """

    # Create a new DataFrame with the desired columns
    result = pd.DataFrame(columns=['Employee Name', 'Week of Year', 'Holiday Hours', 'Regular Hours', 'Overtime Hours'])

    df['Employee Name'] = df['Employee Name'].str.strip() #removes any white spaces that may be created by mistake
    
    # Group the data by employee and week of year
    grouped = df.groupby(['Employee Name', 'Week of year'])
    
    # Iterate over each group and calculate the hours
    for name, group in grouped:
        holiday_hours = group[group['holiday'] == 1]['Hours Worked'].sum()
        regular_hours = group[group['holiday'] == 0]['Hours Worked'].sum()
        overtime_hours = 0
        if regular_hours > 40:
            overtime_hours = regular_hours - 40
            regular_hours = 40
            
            
        result = result.append({'Employee Name': name[0], 'Week of Year': name[1], 'Holiday Hours': holiday_hours, 'Regular Hours': regular_hours, 'Overtime Hours': overtime_hours}, ignore_index=True)

    return result

def process_hours_show_month_year(df):
    """
    Takes a dataframe and categorizes the total hours by each employee into three categories (holliday, regular and overtime hours)

    """

    # Create a new DataFrame with the desired columns
    result = pd.DataFrame(columns=['Employee Name', 'Year', 'Month', 'Holiday Hours', 'Regular Hours', 'Overtime Hours'])

    df['Employee Name'] = df['Employee Name'].str.strip() #removes any white spaces that may be created by mistake
    
    # Group the data by employee and week of year
    grouped = df.groupby(['Employee Name', 'Week of year'])
    
    # Iterate over each group and calculate the hours
    for name, group in grouped:
        holiday_hours = group[group['holiday'] == 1]['Hours Worked'].sum()
        regular_hours = group[group['holiday'] == 0]['Hours Worked'].sum()
        overtime_hours = 0
        if regular_hours > 40:
            overtime_hours = regular_hours - 40
            regular_hours = 40
            
            
        result = result.append({'Employee Name': name[0], 'Week of Year': name[1], 'Holiday Hours': holiday_hours, 'Regular Hours': regular_hours, 'Overtime Hours': overtime_hours}, ignore_index=True)

def convert_df(df):
    df = df.sort_values(by="Employee Name", ascending=True)
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

def transform_schedule_week2(file_name, sheet_name):
    """ This function transforms the user input schedule into a format that can be further analyzed
    
    parameters: 
    file_name: excel or xlsx file format
    sheet_name: name of the sheet as in excel file

    returns:
    A dataframe that contains four columns, employee name, date, hour in, hour out

    """
    #read excel file
    df = pd.read_excel(file_name, sheet_name= sheet_name)

    #remove first row which usually contains the name of the building for ex. hamilton cove
    df = df.iloc[1:]

    #replace null values with a string called unknown, this will help us down the road
    df= df.replace(np.NaN, "Unknown").reset_index(drop=True).iloc[:,1:].reset_index(drop=True)

    # #find the index of the first week, from here you will determine where the first week starts 
    index_of_first_week = df[df['Unnamed: 1'].str.contains("Date") == True].index[0]
    index_of_second_week = df[df['Unnamed: 1'].str.contains("Date") == True].index[1]

    # #rename columns of the dataframe to match that the row of where the first week starts, the columns are now dates that start from 1/16 to 1/22 (first week only)
    df.columns = df.iloc[index_of_second_week]
    df = df.iloc[index_of_second_week:, : ].reset_index(drop=True)

    #lets drop any unknown value in the Date column, if there are no employees why keep it?
    #The date column is just called DATE but in reality that column contains names of each employee
    df = df[df['Date'] !="Unknown"].reset_index(drop =True)
    df = df[df['Date'] !="Name of Employee"].reset_index(drop =True)
    df = df[df['Date'] !="Date"].reset_index(drop =True)
    
    #unpivot the date while fixing the name of the employee
    melt_df = pd.melt(df, id_vars="Date")
    
    #clean up the melt dataframe by removing any employee without work hours, and remove any text like the word "day"
    melt_df = melt_df[melt_df['value'] !="Unknown"].reset_index(drop =True)
    melt_df = melt_df[melt_df['Date'] !="Day"].reset_index(drop =True)

    #some rows that contain total hours get pulled in, but we only need the time worked, our strategy to keep only hourly date was to focus on strings with the : format
    melt_df['value'] = melt_df['value'].astype("str")
    melt_df = melt_df[melt_df['value'].str.contains(":")]

    #rename some of the columns
    melt_df = melt_df.rename(columns={"Date":"Employee Name", "value":"Hours"})
    melt_df.columns.values[1] = "Date"
  

    # we found an interesting pattern, if the Date had an unknown string, that meant that the this is the time out, but if they had a time instead, that meant time in. 
    # so we split the data into test_df1 and test_df2 that we could then merge
    df1 = melt_df[melt_df['Date'] != "Unknown"].reset_index(drop=True)
    df1 = df1.rename(columns={"Hours":"Time In"})
    
    df2 = melt_df[melt_df['Date'] == "Unknown"].reset_index(drop=True)
    df2 = df2.rename(columns={"Hours":"Time Out"})
    df2 = df2[["Time Out"]]
    
    merged_df = pd.merge(left=df1, right=df2, left_index=True, right_index=True)

    return   merged_df

def extract_hourly_rates(file_name , sheet_name):

    """
    This function extracts the hourly rates of each employee in a schedule and aggregates the data by employee.
    """
    #read excel file from the file name and sheet name path
    df = pd.read_excel(file_name, sheet_name)
    #remove any text that contains employee, day, employees, date, total hours from column 17 (total hours) and column index 1 (employee name)
    df = df[~df.iloc[:, 17].astype(str).str.contains("Employees|Day|Employee|Date|total hours", na=False) & 
                    ~df.iloc[:, 1].astype(str).str.contains("Employees|Day|Employee|Date|total hours", na=False)]
    #r column is the hourly rate column, drop all na and turn to a list
    r_column = df.iloc[:, 17].dropna().tolist()
    #b column is the employee name column, drop all na and turn to a list
    b_column = df.iloc[:, 1].dropna().tolist()
    #create a new dataframe and name it hourly rates df, transpose it and rename the columns to human readable values
    hourly_rates_df = pd.DataFrame([r_column, b_column]).T.rename(columns={0:"Hourly Rate", 1:"Employee Name"})
    #change data type of hourly rate into float
    hourly_rates_df['Hourly Rate'] = hourly_rates_df['Hourly Rate'].astype("float")
    #group by employee name and get the average of hourly rate
    hourly_rates_df = hourly_rates_df.groupby("Employee Name").agg({"Hourly Rate":"mean"}).reset_index()
    #set the employee name to be the index 
    hourly_rates_df = hourly_rates_df.set_index("Employee Name")

    return hourly_rates_df

def find_employee_names(df):
    names = df['Employee Name'].apply(lambda x: f"{x.split()[-1]} {x.split()[0]}")
    return names

def process_hours_version_2(df):
    """
    Takes a dataframe and categorizes the total hours by each employee into three categories (holliday, regular and overtime hours)

    """

    # Create a new DataFrame with the desired columns
    result = pd.DataFrame(columns=['Employee Name', 'Month', 'Holiday Hours', 'Regular Hours', 'Overtime Hours'])

    df['Employee Name'] = df['Employee Name'].str.strip() #removes any white spaces that may be created by mistake
    
    # Group the data by employee and week of year
    grouped = df.groupby(['Employee Name', 'Week of year', 'Year', 'Month', 'Building Name'])
    
    # Iterate over each group and calculate the hours
    for name, group in grouped:
        holiday_hours = group[group['holiday'] == 1]['Hours Worked'].sum()
        regular_hours = group[group['holiday'] == 0]['Hours Worked'].sum()
        overtime_hours = 0
        if regular_hours > 40:
            overtime_hours = regular_hours - 40
            regular_hours = 40
        
        month = group.loc[:,'Month']
            
            
        result = result.append({'Employee Name': name[0], 'Month': name[3], 'Year':name[2], 'Building Name': name[4], 'Holiday Hours': holiday_hours, 'Regular Hours': regular_hours, 'Overtime Hours': overtime_hours}, ignore_index=True)

    return result

def extract_hourly_rates(file_name , sheet_name):

    """
    This function extracts the hourly rates of each employee in a schedule and aggregates the data by employee.
    """
    #read excel file from the file name and sheet name path
    df = pd.read_excel(file_name, sheet_name)
    #remove any text that contains employee, day, employees, date, total hours from column 17 (total hours) and column index 1 (employee name)
    df = df[~df.iloc[:, 17].astype(str).str.contains("Employees|Day|Employee|Date|total hours", na=False) & 
                    ~df.iloc[:, 1].astype(str).str.contains("Employees|Day|Employee|Date|total hours", na=False)]
    # #r column is the hourly rate column, drop all na and turn to a list
    r_column = df.iloc[:, 17].dropna().tolist()
    # #b column is the employee name column, drop all na and turn to a list
    b_column = df.iloc[:, 1].dropna().tolist()
    # #create a new dataframe and name it hourly rates df, transpose it and rename the columns to human readable values
    hourly_rates_df = pd.DataFrame([r_column, b_column]).T.rename(columns={0:"Hourly Rate", 1:"Employee Name"})
    # #change data type of hourly rate into float
    hourly_rates_df['Hourly Rate'] = hourly_rates_df['Hourly Rate'].astype("float")
    # #group by employee name and get the average of hourly rate
    hourly_rates_df = hourly_rates_df.groupby("Employee Name").agg({"Hourly Rate":"mean"}).reset_index()
    # #set the employee name to be the index 
    hourly_rates_df = hourly_rates_df.set_index("Employee Name")

    return hourly_rates_df.fillna(17)

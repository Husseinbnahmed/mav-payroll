import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta, time
import re
import helper_functions as x
import altair as alt
import plotly.express as px

#configures the page layout
st.set_page_config(layout="wide", page_title="Maverick Payroll Bot", page_icon="logo_transparent.png")

st.title(""" 🤖 Maverick Payroll Bot""")
st.caption("""
Get ready to take your payroll game to the next level with the Maverick Payroll bot!
 It's a powerhouse that accurately tallies up every employee's hours like a boss, even 
 if they've worked at multiple locations. This bot's lightning-fast processing speed outpaces a human's manual calculation by a whopping 7 times - 
 it's the ultimate solution for payroll domination!
""")
# Streamlit side bar with a logo
with st.sidebar:
    st.sidebar.image("logo_transparent.png")

# List of holiday dates provided by Matt
holidays = ['2023-11-23', '2023-11-25', '2023-12-31', '2023-07-04', '2023-05-29', '2023-09-04']
#list holds cleaned files from first week work schedules, used in for loop 
df_list = [] 
#list holds cleaned files from second week work schedules
df_list_week_two = []
#list holds hourly pay rates for each employee, average of first and second week pay rate
hourly_rates_list = []


with st.form(key='my_form'):
    ##### USER INPUT #########
    st.subheader("1- Upload your excel files")
    files_names = st.file_uploader("📗 Choose an excel file to upload", accept_multiple_files = True, help="You can upload multiple files at once")
    submit_button = st.form_submit_button(label='🧮 Check number of files uploaded')
    if submit_button:
    #write the number of files uploaded
        st.write(len(files_names), "files uploaded")
    else:
    #if no files uploaded, print 0
        st.write("No files uploaded")
    
    st.write("                                                       ")
    st.subheader("2- Provide the name of the tab in your excel file")
    try:
       sheet_name = st.text_input("📄 example: 1-16 to 1-29", help="Make sure it matches exactly your tab name in the excel file")
    except:
       st.warning("Tab name is not found")
      
    st.write("""                                                                         """)
    st.subheader("3-Submit")
    submit_button = st.form_submit_button(label='✅ Submit')

    #if files are uploaded, clean them and save them in a list  
    if submit_button:

        # for each file in the files uploaded (bi-weekly schedules)
            #clean file in a suitable format for further analysis
            #save each file in a list
        for file in files_names: 

            #cleans xlsx file in a format that helps in calculating hours worked by employee
            transformed_file = x.transform_schedule(file, sheet_name=sheet_name) 
            transformed_file_week2 = x.transform_schedule_week2(file, sheet_name=sheet_name)
            hourly_rates_function = x.extract_hourly_rates(file, sheet_name=sheet_name)
            

            #returns the building name associated w each xlsx file
            building_name = x.get_building_name(file, sheet_name) 
            # adds building name to both weeks
            transformed_file['Building Name'] = building_name 
            transformed_file_week2['Building Name'] = building_name

            #saves cleaned file in a list
            df_list.append(transformed_file)
            df_list_week_two.append(transformed_file_week2)
            hourly_rates_list.append(hourly_rates_function)

            #prints success for user! 
            st.success("Successfully uploaded {}".format(file.name))

    else:
        #avoids printing error to user, instead says no file uploaded
        st.caption(" No files uploaded")

try: 

    #combines cleaned xlsx files from each building into one dataframe called "df"
    df_week_one = pd.concat(df_list, axis=0) 
    df_week_two = pd.concat(df_list_week_two, axis=0)
    df = pd.concat([df_week_one, df_week_two], axis=0)

    #Builds a dataframe for employee hourly $ rates, will be used later to calculate the tot. cost per employee
    hourly_rates_df = pd.concat(hourly_rates_list, axis=0)


    # Adds important columns to be used in next steps
    df['holiday'] = df['Date'].apply(lambda x: 1 if x.date().isoformat() in holidays else 0) 
    df['Date'] = pd.to_datetime(df['Date']) 
    df['Week of year'] = df['Date'].apply(lambda x: x.isocalendar()[1])
    df['Year'] = df['Date'].apply(lambda x: x.year)
    df['Month'] = df['Date'].apply(lambda x: x.month)

    # calculates hours worked by employee by building by week
    df = x.hours_worked(df) 

    # returns a dataframe breaking down tot. hours worked into regular, overtime and holiday hours by employee for each week
    final_df = x.process_hours(df)

    # final view! user sees each employee's total holiday, regular and overtime hours
    grouped_final_view = final_df.groupby("Employee Name").agg({"Holiday Hours":"sum", "Regular Hours":"sum", "Overtime Hours":"sum"})
    grouped_final_view = grouped_final_view.reset_index(drop=False)
    grouped_final_view['Employee Name'] = x.find_employee_names(grouped_final_view)
    st.dataframe(grouped_final_view.style.format({'Holiday Hours': '{:,.1f}', 'Regular Hours': '{:,.1f}', 'Overtime Hours': '{:,.1f}'}), width=1000) #render result on streamlit 

    #download to csv
    prcs_csv = x.convert_df(grouped_final_view)
    st.download_button(
        label=":arrow_down: Download to excel",
        data=prcs_csv,
        file_name='auto-report.csv',
        mime='text/csv',)
   

    #plotly chart visualizes hours worked by each building
    st.write("                                      ")
    st.title("📊 Summary of hours worked by building")
    st.caption("The bar chart below summarizes the number of hours worked in each building during the period {}".format(sheet_name))
    visual_df = df.groupby(["Building Name"]).agg({"Hours Worked":"sum"}).reset_index().sort_values(by="Hours Worked", ascending=True)
    fig = px.bar(visual_df, x='Hours Worked', y='Building Name')
    st.plotly_chart(fig, use_container_width=True)


    # calculates payroll in $ by building, accounts for overtime/holiday as 1.5x
    st.write("                                     ")
    st.title("💵 Summary of payroll by building in $")
    st.caption("The data below shows the $ spent by building on employees, broken down by Regular, OT and Holiday hours for the period {}".format(sheet_name))
    df = x.process_hours_version_2(df)
    df = df.join(hourly_rates_df, on="Employee Name", how="left")
    df['Regular Hours Pay'] = df['Regular Hours'] * df['Hourly Rate']
    df['Overtime Pay'] = df['Overtime Hours'] * (df['Hourly Rate'] * 1.5)
    df['Holiday Pay'] = df['Holiday Hours'] * (df['Hourly Rate'] * 1.5)
    df['Total Pay'] = df['Overtime Pay'] + df['Holiday Pay'] + df['Regular Hours Pay']
    df = df.groupby(['Building Name', 'Month', 'Year']).agg({"Total Pay":"sum", "Overtime Pay":"sum", "Regular Hours Pay":"sum", "Holiday Pay":"sum"})
    df = df.reset_index()
    df['Year'] = df['Year'].astype("str")
    df['Building Name'] = df['Building Name'].str.replace('Employees', '').str.replace('Rover', '').str.replace('Valet','').str.strip()
    st.dataframe(df, width=1000)

    #download to csv
    cost_csv = df.to_csv().encode('utf-8')
    st.download_button(
        label=":arrow_down: Download to excel",
        data=cost_csv,
        file_name='payroll_by_building.csv',
        mime='text/csv',)

except:
    #if no file uploaded, prints error message
    st.warning("Please upload a file before proceeding.")




    

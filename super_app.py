import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta, time
import re
import helper_functions as x
import altair as alt

st. set_page_config(layout="wide") 
st.title(""" How It Works 	:grey_question:""")
st.caption("""
To get started, simply upload files/schedules in excel format. 
""")

with st.sidebar:
    st.sidebar.image("logo_transparent.png")

# Create a list of holiday dates
holidays = ['2023-11-23', '2023-11-25', '2023-12-31', '2023-07-04', '2023-05-29', '2023-09-04']
df_list = [] #acts as a database
df_list_week_two = []


with st.form(key='my_form'):
    st.subheader("1- Upload Time Sheets")

    files_names = st.file_uploader("📗 Choose an excel file to upload", accept_multiple_files = True, help="You can upload multiple files at once")
    st.write("                                                       ")
    st.subheader("2- Provide sheet name ")
    sheet_name = st.text_input("📄 example: 1-16 to 1-29", help="Make sure it matches exactly your tab name in the excel file")

    st.write("""                                                                         """)
    st.subheader("3-  Click Submit")
    submit_button = st.form_submit_button(label='✅ Submit')
    if submit_button:
        for file in files_names: #iterate through the user uploaded files
            transformed_file = x.transform_schedule(file, sheet_name=sheet_name) #apply transformation function to each file that will calculate the hours worked
            transformed_file_week2 = x.transform_schedule_week2(file, sheet_name=sheet_name)

            building_name = x.get_building_name(file, sheet_name) #bring in the name of the building
            transformed_file['Building Name'] = building_name #add a building name column to the dataframe
            transformed_file_week2['Building Name'] = building_name
            df_list.append(transformed_file) #save returned dataframe to a list named df_list
            df_list_week_two.append(transformed_file_week2)

    else:
        st.caption(" No files uploaded")

try: 
    df_week_one = pd.concat(df_list, axis=0) #stack all files together
    df_week_two = pd.concat(df_list_week_two, axis=0)
    df = pd.concat([df_week_one, df_week_two], axis=0)

    df['holiday'] = df['Date'].apply(lambda x: 1 if x.date().isoformat() in holidays else 0) #adds a column that has the holidays in it
    df['Date'] = pd.to_datetime(df['Date'])
    df['Week of year'] = df['Date'].apply(lambda x: x.isocalendar()[1])
    df = x.hours_worked(df) #apply the hours worked function to determine by employee
    final_df = x.process_hours(df)
    grouped_final_view = final_df.groupby("Employee Name").agg({"Holiday Hours":"sum", "Regular Hours":"sum", "Overtime Hours":"sum"})

    st.dataframe(grouped_final_view.style.format({'Holiday Hours': '{:,.1f}', 'Regular Hours': '{:,.1f}', 'Overtime Hours': '{:,.1f}'}), width=1000) #render result on streamlit 

    prcs_csv = x.convert_df(grouped_final_view)
    st.download_button(
        label=":arrow_down: Download to excel",
        data=prcs_csv,
        file_name='auto-report.csv',
        mime='text/csv',)
   
    st.write("                                      ")
    st.markdown("### Summary of hours worked by building")

    visual_df = df.groupby(["Building Name"]).agg({"Hours Worked":"sum"}).reset_index()

    c = alt.Chart(visual_df).mark_bar().encode(x = "Hours Worked", y="Building Name")
    c_text = c.mark_text(align="left", baseline="middle", dx=3).encode(text="Hours Worked:Q")
    c_figure = (c + c_text).properties(height=300, width=900)
    st.altair_chart(c_figure)

    #checks and balances 
    #week one dates uploaded and processed

except:
    st.warning("Please upload a file before proceeding.")
    


    

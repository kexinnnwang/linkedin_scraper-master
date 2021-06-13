from linkedin_scraper import Person, actions
from selenium import webdriver
import csv
from helium import *
import pandas as pd
import time

companies = pd.read_csv('founder_links.csv')

links = companies['linkedin_profile_link'].tolist()
column_name = ['Name','About', 'Title', 'Company Name', 'Link', 'Dates Employed', 
'Employment Duration','School', 'Degree Name', 'Field Of Study', 'Dates attended or expected graduation', 'Language']

driver = start_chrome()

email = "mlvc9892@hotmail.com"
password = "Mlvc9892!"
actions.login(driver, email, password) # if email and password isnt given, it'll prompt in terminal

person = Person("https://www.linkedin.com/in/buzzandersen", driver=driver, close_on_complete=False)
df = pd.DataFrame(dict([(k,pd.Series(v , dtype='object')) for k,v in person.data.items()]), columns = column_name)

# test cases not working
# https://www.linkedin.com/in/christopher-quek-li-wen/?originalSubdomain=sg
# https://www.linkedin.com/in/huilinchin/


# for linkedin data
# data = []

# for link in links:
#     if link != 'nil':
#         person = Person(link, driver=driver, close_on_complete=False)
#         output = pd.DataFrame(dict([(k, pd.Series(v, dtype='object')) for k,v in person.data.items()]), columns = column_name)
#         data.append(output)

# df = pd.concat(data)

df.to_csv('linkedin_data.csv', index=False)
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from helium import *
from .objects import Experience, Education, Scraper, Interest, Accomplishment, Contact
import os
import csv
import time


class Person(Scraper):
    __TOP_CARD = "pv-top-card"
    __WAIT_FOR_ELEMENT_TIMEOUT = 5

    def __init__(
            self,
            linkedin_url=None,
            name=None,
            about=None,
            jobs=None,
            schools=None,
            driver=None,
            data=None,
            get=True,
            scrape=True,
            close_on_complete=True,
    ):
        self.linkedin_url = linkedin_url
        self.name = name
        self.about = about or []
        self.jobs = jobs or {}
        self.schools = schools or {}
        self.data = data or {}
        self.also_viewed_urls = []

        if driver is None:
            try:
                if os.getenv("CHROMEDRIVER") == None:
                    driver_path = os.path.join(
                        os.path.dirname(__file__), "drivers/chromedriver"
                    )
                else:
                    driver_path = os.getenv("CHROMEDRIVER")

                driver = webdriver.Chrome(driver_path)
            except:
                driver = webdriver.Chrome()

        if get:
            driver.get(linkedin_url)

        self.driver = driver

        if scrape:
            self.scrape(close_on_complete)

    def add_about(self, about):
        self.about.append(about)

    def add_jobs(self, exp):
        self.jobs = exp

    def add_schools(self, edu):
        self.schools = edu

    def add_location(self, location):
        self.location = location
    
    def add_data(self, persondata):
        self.data = persondata

    def get_duration_months(self, duration):
        time = duration.split(" ")
        if len(time) == 4:
            time_in_months = int(time[0]) * 12 + int(time[2])
          
        else: 
            time_in_months = int(time[0]) * 12 
        return time_in_months

    def have_common(self, list1, list2):
        result = False
        for x in list1:
            for y in list2:
                if x == y:
                    result = True
                    return result 
                    
        return result

    def scrape(self, close_on_complete=True):
        if self.is_signed_in():
            self.scrape_logged_in(close_on_complete=close_on_complete)
        else:
            print("you are not logged in!")
            x = input("please verify the capcha then press any key to continue...")
            self.scrape_not_logged_in(close_on_complete=close_on_complete)

    def _click_see_more_by_class_name(self, class_name):
        try:
            time.sleep(2)
            # if EC.presence_of_element_located((By.CLASS_NAME, class_name)):
            #     print('smth')
            _ = WebDriverWait(self.driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, class_name))
            )
            div = self.driver.find_element_by_class_name(class_name)
            div.find_element_by_tag_name("button").click()
        except Exception as e:
            pass
            # print(e)
            # print('hi')

    def scrape_logged_in(self, close_on_complete=True, sleep_duration=2):
        driver = self.driver
        duration = None

        root = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located(
                (
                    By.CLASS_NAME,
                    self.__TOP_CARD,
                )
            )
        )

        header = ['Name','About', 'Title', 'Company Name', 'Link', 'Dates Employed', 
        'Employment Duration','School', 'Degree Name', 'Field Of Study', 'Dates attended or expected graduation', 'Language']

        data = {k: [] for k in header}

        # get name
        name = root.find_elements_by_xpath(
             "//*[starts-with(@class, 'text-heading-xlarge inline t-24 v-align-middle break-words')]")[0].text.strip()

        data['Name'].append(name)

        # get about
        if Button('see more').exists():
            click(Button('see more'))
            time.sleep(sleep_duration)
        about = [cell.web_element.text for cell in find_all(S('div > div > div > section > div', below='About'))]
        if len(about) > 0:
            data['About'].append(about[0])
        # scroll to end in order to populate the html content
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(4)

        # get all the main cards        
        main_card_sections = find_all(S('.background-details > div > section > div > section'))

        # scroll back up
        driver.execute_script('window.scrollTo(0, -document.body.scrollHeight);')
        time.sleep(4)

        #print(main_card_sections)

        for c in main_card_sections:
            #print(c)
            element = c.web_element
            header = element.find_element_by_tag_name('header')
            header_text = header.text
            print(header_text) ## this should be your key

            try:
                button = element.find_element_by_xpath('./div/button')
                ActionChains(driver).move_to_element(button).perform()
                time.sleep(2)
                button.click()
            except NoSuchElementException:
                pass 

            # get experience 
            if header_text == 'Experience':
                entries = element.find_elements_by_xpath('./ul/li/section')
                exp_keys = ['Title', 'Company Name', 'Link', 'Dates Employed', 'Employment Duration']
                all_entry = []
                for e in entries:
                    if not len(e.find_elements_by_tag_name('li')):
                        k = e.text.strip().split('\n')
                        all_entry.append(k)
        
                    else:
                        print("entry with extension")
                        # check for nested button
                        try:
                            button_exp = e.find_element_by_xpath('./div/button')
                            ActionChains(driver).move_to_element(button_exp).perform()
                            time.sleep(2)
                            button_exp.click()
                        except NoSuchElementException:
                            pass   
                        k = e.text.strip().split('\n')
                        all_entry.append(k)
                        
                # update experience into dictionary
                for exp in all_entry:
                    temp = []
                    for count in range(len(exp)):
                        text = str(exp[count])
                        if text in data.keys():
                            temp.append(text)
                            if text == 'Employment Duration':
                                duration = exp[count+1]
                                data[text].append(self.get_duration_months(duration))
                            elif text == 'Company Name':
                                data[text].append(exp[count+1])
                                data['Link'].append(Link(exp[0]).web_element.get_attribute('href'))
                                temp.append('Link')
                                if exp.count('Title') > 1:
                                    data[text].extend(exp[count+1] for j in range(exp.count('Title') - 1))
                            else:
                                data[text].append(exp[count+1])                   
                        elif count == 0:
                            data['Title'].append(text)
                            temp.append('Title')
                for key in exp_keys:
                    if key not in temp:
                        data[key].append('None')

            # get education
            elif header_text == 'Education':
                entries = element.find_elements_by_xpath('./ul/li/div')
                edu_keys = ['School', 'Degree Name', 'Field Of Study', 'Dates attended or expected graduation']
                all_entry = []
                for e in entries:
                    if not len(e.find_elements_by_tag_name('li')):
                        k = e.text.strip().split('\n')
                        all_entry.append(k)
                    else:
                        print("entry with extension")
                        # check for nested button
                        try:
                            button_edu = e.find_elements_by_xpath('./div/button')
                            for i in button_edu:
                                ActionChains(driver).move_to_element(i).perform()
                                time.sleep(2)
                                i.click()
                        except NoSuchElementException:
                            pass   
                        k = e.text.strip().split('\n')
                        all_entry.append(k)

                for edu in all_entry:
                    temp = []
                    for i in edu :
                        #i = str(i)
                        if i in data.keys():
                            index = edu.index(i)
                            temp.append(i)
                            data[i].append(edu [index+1])
                        elif edu .index(i) == 0:
                            data['School'].append(i)
                            temp.append('School')
                    for key in edu_keys:
                        if key not in temp:
                            data[key].append('None')
        #print(data)
        #get language
        #language = find_all(S('.background-details > div > section > div > section'))
        # if button:
        #     for i in button:
        #         click(i)
        languages = [cell.web_element.text for cell in find_all(S('div > div > div > section > div > section > div', below='Accomplishments'))]

        for element in languages:
            element = element.split("\n")
            if (element[0] == 'Languages') or (element[0] == 'Language'):
                for count in range(1, len(element)):
                    if element[count] == 'Language name':
                        data['Language'].append(element[count + 1])
                if not data['Language']:
                    for j in element[1:]:
                        data['Language'].append(j)
        
        # store data
        self.add_data(data)
        

    def scrape_not_logged_in(self, close_on_complete=True, retry_limit=10, sleep_duration=2):
        driver = self.driver
        retry_times = 0
        while self.is_signed_in() and retry_times <= retry_limit:
            page = driver.get(self.linkedin_url)
            retry_times = retry_times + 1

        root = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located(
                (
                    By.CLASS_NAME,
                    self.__TOP_CARD,
                )
            )
        )

        header = ['Name','About', 'Title', 'Company Name', 'Link', 'Dates Employed', 
        'Employment Duration','School', 'Degree Name', 'Field Of Study', 'Dates attended or expected graduation', 'Language']

        data = {k: [] for k in header}

        # get name
        name = root.find_elements_by_xpath(
             "//*[starts-with(@class, 'text-heading-xlarge inline t-24 v-align-middle break-words')]")[0].text.strip()

        data['Name'].append(name)

        # get about
        if Button('see more').exists():
            click(Button('see more'))
            time.sleep(sleep_duration)
        about = [cell.web_element.text for cell in find_all(S('div > div > div > section > div', below='About'))]
        if len(about) > 0:
            data['About'].append(about[0])

         # scroll to end in order to populate the html content
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(2)

        # get all the main cards        
        main_card_sections = find_all(S('.background-details > div > section > div > section'))

        # scroll back up
        driver.execute_script('window.scrollTo(0, -document.body.scrollHeight);')
        time.sleep(2)

        for c in main_card_sections:
            element = c.web_element
            header = element.find_element_by_tag_name('header')
            header_text = header.text
            print(header_text) ## this should be your key

            # get experience 
            if  header_text == 'Experience':
                entries = element.find_elements_by_xpath('./ul/li/section')
                exp_keys = ['Title', 'Company Name', 'Link', 'Dates Employed', 'Employment Duration']
                all_entry = []
                for e in entries:
                    if not len(e.find_elements_by_tag_name('li')):
                        k = e.text.strip().split('\n')
                        all_entry.append(k)
        
                    else:
                        print("entry with extension")
                        # check for nested button
                        try:
                            button_exp = e.find_element_by_xpath('./div/button')
                            ActionChains(driver).move_to_element(button_exp).perform()
                            time.sleep(2)
                            button_exp.click()
                        except NoSuchElementException:
                            pass   
                        k = e.text.strip().split('\n')
                        all_entry.append(k)
                        
                # update experience into dictionary
                for exp in all_entry:
                    temp = []
                    for count in range(len(exp)):
                        text = str(exp[count])
                        if text in data.keys():
                            temp.append(text)
                            if text == 'Employment Duration':
                                duration = exp[count+1]
                                data[text].append(self.get_duration_months(duration))
                            elif text == 'Company Name':
                                data[text].append(exp[count+1])
                                data['Link'].append(Link(exp[0]).web_element.get_attribute('href'))
                                temp.append('Link')
                                if exp.count('Title') > 1:
                                    data[text].extend(exp[count+1] for j in range(exp.count('Title') - 1))
                            else:
                                data[text].append(exp[count+1])                   
                        elif count == 0:
                            data['Title'].append(text)
                            temp.append('Title')
                for key in exp_keys:
                    if key not in temp:
                        data[key].append('None')

            # get education
            elif header_text == 'Education':
                entries = element.find_elements_by_xpath('./ul/li/div')
                edu_keys = ['School', 'Degree Name', 'Field Of Study', 'Dates attended or expected graduation']
                all_entry = []
                for e in entries:
                    if not len(e.find_elements_by_tag_name('li')):
                        k = e.text.strip().split('\n')
                        all_entry.append(k)
                    else:
                        print("entry with extension")
                        # check for nested button
                        try:
                            button_edu = e.find_elements_by_xpath('./div/button')
                            for i in button_edu:
                                ActionChains(driver).move_to_element(i).perform()
                                time.sleep(2)
                                i.click()
                        except NoSuchElementException:
                            pass   
                        k = e.text.strip().split('\n')
                        all_entry.append(k)

                for edu in all_entry:
                    temp = []
                    for i in edu :
                        #i = str(i)
                        if i in data.keys():
                            index = edu.index(i)
                            temp.append(i)
                            data[i].append(edu [index+1])
                        elif edu .index(i) == 0:
                            data['School'].append(i)
                            temp.append('School')
                    for key in edu_keys:
                        if key not in temp:
                            data[key].append('None')
        print(data)
        #get language
        #language = find_all(S('.background-details > div > section > div > section'))
        # if button:
        #     for i in button:
        #         click(i)
        languages = [cell.web_element.text for cell in find_all(S('div > div > div > section > div > section > div', below='Accomplishments'))]

        for element in languages:
            element = element.split("\n")
            if (element[0] == 'Languages') or (element[0] == 'Language'):
                for count in range(1, len(element)):
                    if element[count] == 'Language name':
                        data['Language'].append(element[count + 1])
                if not data['Language']:
                    for j in element[1:]:
                        data['Language'].append(j)
        
        # store data
        self.add_data(data)

    @property
    def company(self):
        if self.experiences:
            return (
                self.experiences[0].institution_name
                if self.experiences[0].institution_name
                else None
            )
        else:
            return None

    @property
    def job_title(self):
        if self.experiences:
            return (
                self.experiences[0].position_title
                if self.experiences[0].position_title
                else None
            )
        else:
            return None
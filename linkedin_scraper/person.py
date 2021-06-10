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


        ################################################################################################################
        # scroll to end in order to populate the html content
        # driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')

        # # get all the main cards        
        # main_card_sections = find_all(S('.background-details > div > section > div > section'))

        # # scroll back up
        # driver.execute_script('window.scrollTo(0, -document.body.scrollHeight);')

        # for c in main_card_sections:
        #     element = c.web_element
        #     header = element.find_element_by_tag_name('header')
        #     header_text = header.text
        #     print(header_text) ## this should be your key

        #     try:
        #         button = element.find_element_by_xpath('./div/button')
        #         ActionChains(driver).move_to_element(button).perform()
        #         time.sleep(2)
        #         button.click()
        #     except NoSuchElementException:
        #         pass    

        #     entries = element.find_elements_by_xpath('./ul/li/section')
        #     for e in entries:
        #         if not len(e.find_elements_by_tag_names('li')):
        #             print("no extension")
        #             ## add the logic for entries without nested rows
        #         else:
        #             print("entry with extension")
        #             # check for nested button
        #             try:
        #                 pass
        #                 # try to expand if there are too many
        #                 ## some nested element here, replace with the element
        #                 # button = element.find_element_by_xpath('./div/button')
        #                 # ActionChains(driver).move_to_element(button).perform()
        #                 # time.sleep(2)
        #                 # button.click()
        #             except NoSuchElementException:
        #                 pass   
        #             ## then scrap the individual lists

        ################################################################################################################

        exp = [cell.web_element.text for cell in find_all(S('span > div > section > div > section > ul > li > section', below='Experience', above='Education'))]

        exp_keys = ['Title', 'Company Name', 'Link', 'Dates Employed', 'Employment Duration']

        for k in exp:
            k = k.split('\n')
            temp = []
            for count in range(len(k)):
                element = str(k[count])
                if element in data.keys():
                    temp.append(element)
                    if element == 'Employment Duration':
                        duration = k[count+1]
                        data[element].append(self.get_duration_months(duration))
                    elif element == 'Company Name':
                        data[element].append(k[count+1])
                        data['Link'].append(Link(k[0]).web_element.get_attribute('href'))
                        temp.append('Link')
                        if k.count('Title') > 1:
                            data[element].append(k[count+1])
                    else:
                        data[element].append(k[count+1])
                            
                elif count == 0:
                    data['Title'].append(element)
                    temp.append('Title')
            for key in exp_keys:
                if key not in temp:
                    data[key].append('None')

        driver.execute_script(
            "window.scrollTo(0, Math.ceil(document.body.scrollHeight/1.5));"
        )

        # get education
        ## Click SEE MORE
        # self._click_see_more_by_class_name("pv-education-section__see-more")
        time.sleep(sleep_duration)

        edu = [cell.web_element.text for cell in find_all(S('div > section > div > section > ul > li > div', below='Education'))]

        edu_keys = ['School', 'Degree Name', 'Field Of Study', 'Dates attended or expected graduation']

        for k in edu:
            k = k.split('\n')
            if self.have_common(k, edu_keys):
                temp = []
                for element in k:
                    element = str(element)
                    if element in data.keys():
                        index = k.index(element)
                        temp.append(element)
                        data[element].append(k[index+1])
                    elif k.index(element) == 0:
                        data['School'].append(element)
                        temp.append('School')
                for key in edu_keys:
                    if key not in temp:
                        data[key].append('None')

        # element = [cell.web_element.text for cell in find_all(S('div > section > div > section > ul', below='Education'))]

        # print(element)

        # length = len([cell.web_element.text for cell in find_all(S('div > section > div > section > ul', below='Education'))][0].split('\n'))

        # count = 0

        # edu_keys = ['School', 'Degree Name', 'Field Of Study', 'Dates attended or expected graduation']

        # for k in edu:
        #     k = k.split('\n')
        #     count += len(k)
        #     temp = []
        #     if count <= length:
        #         for element in k:
        #             element = str(element)
        #             if element in data.keys():
        #                 index = k.index(element)
        #                 temp.append(element)
        #                 data[element].append(k[index+1])
        #             elif k.index(element) == 0:
        #                 data['School'].append(element)
        #                 temp.append('School')
        #         for key in edu_keys:
        #             if key not in temp:
        #                 data[key].append('None')


        #get language
        button = [S('div > div > div > section > div > section > div > button > li-icon')]
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

        # driver.execute_script(
        #     "window.scrollTo(0, Math.ceil(document.body.scrollHeight/1.75));"
        # )

        # get experience

        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')

        # driver.execute_script(
        #     "window.scrollTo(0, Math.ceil(document.body.scrollHeight*2/5));"
        # )
        
        self._click_see_more_by_class_name("pv-profile-section__see-more-inline pv-profile-section__text-truncate-toggle artdeco-button artdeco-button--tertiary artdeco-button--muted")


        # if Button('more experiences').exists():
        #     click(Button('more experiences'))
        #     time.sleep(sleep_duration)

        exp = [cell.web_element.text for cell in find_all(S('span > div > section > div > section > ul > li > section', below='Experience', above='Education'))]

        exp_keys = ['Title', 'Company Name', 'Link', 'Dates Employed', 'Employment Duration']

        for k in exp:
            k = k.split('\n')
            temp = []
            for count in range(len(k)):
                element = str(k[count])
                if element in data.keys():
                    temp.append(element)
                    if element == 'Employment Duration':
                        duration = k[count+1]
                        data[element].append(self.get_duration_months(duration))
                    elif element == 'Company Name':
                        data[element].append(k[count+1])
                        data['Link'].append(Link(k[0]).web_element.get_attribute('href'))
                        temp.append('Link')
                        if k.count('Title') > 1:
                            data[element].append(k[count+1])
                    else:
                        data[element].append(k[count+1])
                            
                elif count == 0:
                    data['Title'].append(element)
                    temp.append('Title')
            for key in exp_keys:
                if key not in temp:
                    data[key].append('None')

        driver.execute_script(
            "window.scrollTo(0, Math.ceil(document.body.scrollHeight/1.5));"
        )

        # get education
        ## Click SEE MORE
        self._click_see_more_by_class_name("pv-education-section__see-more")
        time.sleep(sleep_duration)

        edu = [cell.web_element.text for cell in find_all(S('div > section > div > section > ul > li', below='Education'))]

        edu_keys = ['School', 'Degree Name', 'Field Of Study', 'Dates attended or expected graduation']

        for k in edu:
            k = k.split('\n')
            temp = []
            for element in k:
                element = str(element)
                if element in data.keys():
                    index = k.index(element)
                    temp.append(element)
                    data[element].append(k[index+1])
                elif k.index(element) == 0:
                    data['School'].append(element)
                    temp.append('School')
            for key in edu_keys:
                if key not in temp:
                    data[key].append('None')

        #get language
        button = [S('div > div > div > section > div > section > div > button > li-icon')]
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
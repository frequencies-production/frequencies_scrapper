from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import csv
import os.path

class Scrapper():
    
    @classmethod
    def add_method(cls, fun):
        setattr(cls, fun.__name__, fun)
        return fun
    
    
    def __init__(self, username, password, link):
        super().__init__()
        self.username = username
        self.password = password
        self.link = link
        
        
@Scrapper.add_method
def init_driver(self):
    
    
    driver = webdriver.Chrome()
    return driver

@Scrapper.add_method
def page_navigation(self, driver, waiting_time):
    
    # Navigate through login page
    driver.get(self.link)
    
    # Wait for the login to load
    wait = WebDriverWait(driver, waiting_time)
    email_field = wait.until(EC.presence_of_element_located((By.ID, "user_account_email")))
    password_field = wait.until(EC.presence_of_element_located((By.ID, "user_account_password")))
    
    # Fill in the login form
    email_field.send_keys(self.username)
    password_field.send_keys(self.password)
    
    # Click the login button
    login_button = driver.find_element(By.XPATH, "//input[@value='Log In']") #TODO: Replace by login_input
    login_button.click()

    # Pause to allow time for the page to load
    time.sleep(5)  # Adjust as needed

    # Wait until the user is logged in (check the URL)
    wait.until(EC.url_contains("submissions/my_submissions")) #TODO: Replace by sublink

    print("Logged in successfully!")
    
def extract_data_from_main_topic(main_topic, fields_to_extract: list[str]):
    
    extracted_fields = []
    for i in fields_to_extract:
        result = main_topic.find_element(By.CLASS_NAME, i).text.strip()
        extracted_fields.append(result)
        
    return extracted_fields
    


def extract_data(driver, export_filename):
    
    # Retrieve data  from all pages 
    
    data = []
    while True:
        
        # Retrieve data from ther current page
        submissions = driver.find_elements(By.XPATH, '//*[@id="my-submissions-index"]/div[3]/div[2]/div[@class="tableRow"]') #TODO: Replace by div_elements

        # Extract data from each submission
        for submission in submissions:
            row = extract_data_from_main_topic(submission)
            data.append(row)

        # Check if there is a next page
        try:
            next_button_span = driver.find_element(By.CLASS_NAME, 'next')
            next_button_a = next_button_span.find_element(By.TAG_NAME, 'a')
            next_button_a.click()  # Click next page button
            time.sleep(3)  # Adjust as needed
        except NoSuchElementException:
            break  # No more pages
    
    # Write data to CSV file
    with open(export_filename, 'a', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)

        # Write data rows
        for row in data:
            csv_writer.writerow(row)
            
    # Wait for user input before closing the browser
    input("Press Enter to close the browser...")

    # Close the browser session
    driver.quit()
    
        
        

if __name__ == "__main__":
    print("Hello")
    username = "freqiuencies.production@gmail.com"
    password = "Distrib31!"
    
    link = "https://filmfreeway.com/submissions/my_submissions"
    scrapper = Scrapper(username, password, link)
    scrapper_driver = scrapper.init_driver()
    scrapper.page_navigation(scrapper_driver, 10)
    scrapper_driver.quit()
import time
import csv
import random
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def setup_driver():
    """Set up and return a configured Chrome webdriver."""
    chrome_options = Options()
    # Comment out headless mode for troubleshooting
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Add user agent to mimic real browser
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def human_like_delay():
    time.sleep(random.uniform(0.2, 0.8))

def extract_education_from_skills(skills_list, job_title):
    """Extract education-related items from skills list."""
    education_keywords = ["bachelor", "b.s.", "b.a.", "master", "m.s.", "m.a.", "phd", "ph.d", "doctorate", "doctor", "degree", "education", "diploma", "certificate", "certification", "graduate", "undergraduate", "associate"]

    experience_keywords = ["year", "years"]

    level_keywords = ["junior level", "entry level", "mid level", "mid-level", "senior level"]
    
    actual_skills = []
    education_items = []
    experience_items = []
    level_items = []

    for skill in skills_list:
        # Check if this skill item contains education/experience-related keywords
        is_skill = True
        skill_lower = skill.lower()
        
        for keyword in education_keywords:
            if keyword in skill_lower:
                education_items.append(skill)
                is_skill = False
                break

        for keyword in experience_keywords:
            if keyword in skill_lower:
                experience_items.append(skill)
                is_skill = False
                break

        for keyword in level_keywords:
            if keyword in skill_lower:
                level_items.append(skill)
                is_skill = False
                break
        
        if is_skill:
            actual_skills.append(skill)

    # Also quickly check job title
    if 'sr. ' in job_title or 'senior' in job_title:
        level_items.append('Senior level')
    elif 'jr. ' in job_title or 'junior' in job_title:
        level_items.append('Junior level')
    
    return actual_skills, education_items, experience_items, level_items

def glassdoor_extract_education_from_skills(skills_list, job_title):
    """Messy mod for Glasdoor description extraction."""
    education_keywords = ["bachelor", "b.s.", "b.a.", "master", "m.s.", "m.a.", "phd", "ph.d", "doctorate", "doctor", "degree", "education", "diploma", "certificate", "certification", "graduate", "undergraduate", "associate"]

    experience_keywords = ["year", "years"]

    level_keywords = ["junior level", "entry level", "mid level", "mid-level", "senior level"]
    
    education_items = set()
    experience_items = set()
    level_items = set()

    for skill in skills_list:
        # Check if this skill item contains education/experience-related keywords
        skill_lower = skill.lower()
        
        for keyword in education_keywords:
            if keyword in skill_lower:
                education_items.add(keyword)

        for keyword in experience_keywords:
            if keyword in skill_lower:
                # Find years of experience as 2 words separated by whitespace
                matches = re.findall(r'\S+\s+years', skill_lower)
                for match in matches:
                    experience_items.add(match)

        for keyword in level_keywords:
            if keyword in skill_lower:
                level_items.add(keyword)

    # Also quickly check job title
    if 'sr. ' in job_title or 'senior' in job_title:
        level_items.append('Senior level')
    elif 'jr. ' in job_title or 'junior' in job_title:
        level_items.append('Junior level')
    
    return education_items, experience_items, level_items

def save_to_csv(jobs_data, filename='jobs.csv'):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Job Title', 'Company', 'Location', 'Skills', 'Education', 'Experience', 'Job Level', 'Salary']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for job in jobs_data:
            writer.writerow(job)
    
    print(f'Data saved to {filename}')

files_and_sources = {
    'glassdoor_software_engineer': 'https://www.glassdoor.com/Job/united-states-software-engineer-jobs-SRCH_IL.0,13_KO14,31.htm',
    'glassdoor_software_developer': 'https://www.glassdoor.com/Job/united-states-software-developer-jobs-SRCH_IL.0,13_IN1_KO14,32.htm',
    'glassdoor_data_scientist': 'https://www.glassdoor.com/Job/united-states-data-scientist-jobs-SRCH_IL.0,13_IN1_KO14,28.htm',
    'glassdoor_computer_scientist': 'https://www.glassdoor.com/Job/united-states-computer-scientist-jobs-SRCH_IL.0,13_IN1_KO14,32.htm',
    'simplyhired_software_engineer': 'https://www.simplyhired.com/search?q=software+engineer&l=',
    'simplyhired_software_developer': 'https://www.simplyhired.com/search?q=software+developer&l=',
    'simplyhired_data_scientist': 'https://www.simplyhired.com/search?q=data+scientist&l=',
    'simplyhired_computer_scientist': 'https://www.simplyhired.com/search?q=computer+scientist&l=',
}
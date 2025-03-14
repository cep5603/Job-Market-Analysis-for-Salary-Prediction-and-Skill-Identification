from scraper_utils import *

def scrape_glassdoor_jobs(url, num_pages=5):
    """Scrape job postings from Glassdoor using correct class names."""
    driver = setup_driver()
    jobs_data = []
    processed_job_ids = set()  # Set to keep track of processed job IDs
    
    try:
        # Open the initial URL
        driver.get(url)
        print("Navigating to the page...")
        human_like_delay()  # Give time for the page to load
        
        # Handle cookie consent
        try:
            cookie_selectors = [
                "#onetrust-accept-btn-handler",
                "button[data-test='allow-all']",
                "button.cookieConsent"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    cookie_button.click()
                    print(f"Accepted cookies using selector: {selector}")
                    human_like_delay()
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
        except Exception as e:
            print(f"Cookie handling exception: {e}")
        
        # Handle various popup modals
        modal_close_selectors = [
            "[alt='Close']",
            "button[aria-label='Close']",
            ".modal_closeIcon"
        ]
        
        for selector in modal_close_selectors:
            try:
                close_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                if close_buttons:
                    for button in close_buttons:
                        driver.execute_script("arguments[0].click();", button)
                        print(f"Closed modal using selector: {selector}")
                        human_like_delay()
            except Exception:
                continue
        
        load_count = 0
        target_loads = num_pages - 1  # We already have one page loaded initially
        
        # Wait for initial job list to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'JobsList_')]"))
        )
        human_like_delay()
        
        # First, load all jobs by clicking "Show more jobs" button multiple times
        while load_count < target_loads:
            try:
                # Find the "Show more jobs" button
                load_more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@data-test='load-more']"))
                )
                
                if load_more_button and load_more_button.is_enabled():
                    # Scroll to the button to make sure it's in view
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more_button)
                    human_like_delay()
                    # Click the button
                    driver.execute_script("arguments[0].click();", load_more_button)
                    print(f"Clicked 'Show more jobs' button ({load_count + 1}/{target_loads})")
                    
                    # Wait for new content to load - look for a change in the number of job cards
                    current_count = len(driver.find_elements(By.XPATH, "//li[contains(@class, 'JobsList_jobListItem_')]"))
                    WebDriverWait(driver, 10).until(
                        lambda d: len(d.find_elements(By.XPATH, "//li[contains(@class, 'JobsList_jobListItem_')]")) > current_count
                    )
                    
                    load_count += 1
                    human_like_delay()
                else:
                    print("Load more button not found or disabled, stopping pagination")
                    break
            except Exception as e:
                print(f"Error loading more jobs: {e}")
                break
        
        # Now that all jobs are loaded, process each job card
        job_cards = driver.find_elements(By.XPATH, "//li[contains(@class, 'JobsList_jobListItem_')]")
        print(f"Found {len(job_cards)} total job cards after loading {load_count + 1} pages")
        
        # Process each job card's information
        for i, job_card in enumerate(job_cards):
            try:
                print(f"Processing job {i+1}/{len(job_cards)}")
                job_id = f"job_{i}"
                
                # Skip if we've already processed this job
                if job_id in processed_job_ids:
                    print(f"Skipping already processed job: {job_id}")
                    continue
                
                # Mark this job as processed
                processed_job_ids.add(job_id)
                
                # Extract job details
                job_data = {}
                
                # Extract job title
                try:
                    job_title_elem = job_card.find_element(By.XPATH, ".//*[contains(@class, 'JobCard_jobTitle_')]")
                    job_data["Job Title"] = job_title_elem.text.strip()
                except NoSuchElementException:
                    job_data["Job Title"] = "N/A"
                
                # Extract company name
                try:
                    company_elem = job_card.find_element(By.XPATH, ".//*[contains(@class, 'EmployerProfile_employerName_')]")
                    job_data["Company"] = company_elem.text.strip()
                except NoSuchElementException:
                    try:
                        company_elem = job_card.find_element(By.XPATH, ".//*[contains(@class, 'EmployerProfile_compactEmployerName_')]")
                        job_data["Company"] = company_elem.text.strip()
                    except NoSuchElementException:
                        job_data["Company"] = "N/A"
                
                # Extract location
                try:
                    location_elem = job_card.find_element(By.XPATH, ".//*[contains(@id, 'job-location-')]")
                    job_data["Location"] = location_elem.text.strip()
                except NoSuchElementException:
                    try:
                        location_elem = job_card.find_element(By.XPATH, ".//*[contains(@class, 'location_')]")
                        job_data["Location"] = location_elem.text.strip()
                    except NoSuchElementException:
                        job_data["Location"] = "N/A"
                
                # Extract salary if available
                try:
                    salary_elem = job_card.find_element(By.XPATH, ".//*[contains(@class, 'JobCard_salaryEstimate_')]")
                    job_data["Salary"] = salary_elem.text.strip()
                except NoSuchElementException:
                    job_data["Salary"] = "N/A"
                
                # Extract skills
                skills = "N/A"
                try:
                    desc_elem = job_card.find_element(By.XPATH, ".//*[contains(@class, 'JobCard_jobDescriptionSnippet_')]")
                    skills_div = desc_elem.find_element(By.XPATH, "./div[2]")
                    if "Skills:" in skills_div.text:
                        skills_text = skills_div.text.replace("Skills:", "").strip()
                        if skills_text:
                            skills = skills_text
                except Exception as e:
                    print(f"Error extracting skills: {e}")
                
                job_data["Skills"] = skills
                job_data["Education"] = "N/A"
                job_data["Experience"] = "N/A"
                job_data["Job Level"] = "N/A"

                # Click on the job listing to view details
                try:
                    # Find and click on the job title link to view full details
                    job_title_link = job_card.find_element(By.XPATH, ".//a[@data-test='job-link']")
                    
                    # Scroll into view and click
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", job_title_link)
                    human_like_delay()
                    driver.execute_script("arguments[0].click();", job_title_link)

                    # Wait for job details to load in the right column
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'JobDetails_jobDescription_') or contains(@class, 'jobDetailsContainer')]"))
                    )
                    human_like_delay()
                    
                    # Click "Show more" button to expand the full description
                    try:
                        show_more_buttons = driver.find_elements(By.XPATH, "//span[text()='Show more']/parent::button")
                        if show_more_buttons:
                            button = show_more_buttons[0]
                            if button.is_displayed():
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                                human_like_delay()
                                driver.execute_script("arguments[0].click();", button)
                                print("Clicked 'Show more' button to expand description")
                                show_more_clicked = True
                                human_like_delay()
                                human_like_delay()
                    except Exception as e:
                        print(f"Error trying to click 'Show more' button: {e}")

                    # Extract the full job description
                    try:
                        job_description_elem = driver.find_element(By.XPATH, "//div[contains(@class, 'JobDetails_jobDescription_')]")
                        job_description = job_description_elem.text
                        print(f'FOUND DESCRIPTION:\n{job_description}')
                    except NoSuchElementException:
                        print("Error: NoSuchElementException")
                    
                    # Parse the job description to extract keywords and categorize them
                    description_lines = [line.strip() for line in job_description.split('\n') if line.strip()]
                    
                    print(f'DESCRIPTION LINES:\n{description_lines}\n')

                    # Extract skills, education, experience, and job level from the description
                    education_items, experience_items, level_items = glassdoor_extract_education_from_skills(description_lines, job_data["Job Title"])
                    
                    # Update job data with the extracted information
                    job_data["Education"] = ", ".join(education_items) if education_items else "N/A"
                    job_data["Experience"] = ", ".join(experience_items) if experience_items else "N/A"
                    job_data["Job Level"] = ", ".join(level_items) if level_items else "N/A"
                    
                    print(f"\nExtracted from description - Education: {job_data['Education']}, Experience: {job_data['Experience']}, Level: {job_data['Job Level']}")
                except Exception as e:
                    print(f"Error extracting detailed job information: {e}")
                
                jobs_data.append(job_data)
                print(f"Successfully scraped: {job_data['Job Title']} at {job_data['Company']}")
                
                human_like_delay()
                
            except StaleElementReferenceException:
                print("Element became stale, moving to next job")
                continue
            except Exception as e:
                print(f"Error processing job: {e}")
                continue
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        driver.quit()
    
    return jobs_data

def main():
    output_file_stem = 'glassdoor_software_developer'
    url = files_and_sources[output_file_stem]
    num_pages = 20
    
    print(f'This script will attempt to scrape {num_pages} pages of job listings')
    
    jobs_data = scrape_glassdoor_jobs(url, num_pages)
    
    if jobs_data:
        print(f'Scraped {len(jobs_data)} unique jobs')
        save_to_csv(jobs_data, 'data/' + output_file_stem + '.csv')
    else:
        print('No jobs scraped')

if __name__ == "__main__":
    main()
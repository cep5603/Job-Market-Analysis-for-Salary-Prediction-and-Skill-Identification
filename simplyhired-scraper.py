from scraper_utils import *

def scrape_simplyhired_jobs(url, num_pages=5):
    """Scrape job postings from SimplyHired."""
    driver = setup_driver()
    jobs_data = []
    processed_job_ids = set()  # Set to keep track of processed job IDs
    
    try:
        # Open the initial URL
        driver.get(url)
        print("Navigating to the page...")
        human_like_delay()  # Give time for the page to load
        
        # Handle cookie consent if present
        try:
            cookie_selectors = [
                "button[data-testid='CybotCookiebotDialogBodyButtonAccept']",
                "button.accept-cookies",
                "#onetrust-accept-btn-handler"
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
        
        # Loop through pages
        for page in range(1, num_pages + 1):
            print(f"Scraping page {page} of {num_pages}")
            
            # Wait for job listings to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='searchSerpJob']"))
            )
            human_like_delay()
            
            # Find all job listings on the current page
            job_listings = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='searchSerpJob']")
            print(f"Found {len(job_listings)} job listings on page {page}")
            
            # Process each job listing
            for i, job_listing in enumerate(job_listings):
                try:
                    print(f"Processing job {i+1}/{len(job_listings)} on page {page}")
                    job_id = f"job_{i}_{page}"
                    
                    # Skip if we've already processed this job
                    if job_id in processed_job_ids:
                        print(f"Skipping already processed job: {job_id}")
                        continue
                    
                    # Mark this job as processed
                    processed_job_ids.add(job_id)
                    
                    # Initialize job data dictionary
                    job_data = {}
                    
                    # Extract job title
                    try:
                        job_title_elem = job_listing.find_element(By.CSS_SELECTOR, "h2")
                        job_data["Job Title"] = job_title_elem.text.strip()
                    except NoSuchElementException:
                        job_data["Job Title"] = "N/A"
                    
                    # Extract company name
                    try:
                        company_elem = job_listing.find_element(By.CSS_SELECTOR, "span[data-testid='companyName']")
                        job_data["Company"] = company_elem.text.strip()
                    except NoSuchElementException:
                        job_data["Company"] = "N/A"
                    
                    # Extract location
                    try:
                        location_elem = job_listing.find_element(By.CSS_SELECTOR, "span[data-testid='searchSerpJobLocation']")
                        job_data["Location"] = location_elem.text.strip()
                    except NoSuchElementException:
                        job_data["Location"] = "N/A"
                    
                    # Extract salary if available
                    try:
                        salary_elem = job_listing.find_element(By.CSS_SELECTOR, "p[data-testid='searchSerpJobSalaryConfirmed']")
                        job_data["Salary"] = salary_elem.text.strip()
                    except NoSuchElementException:
                        job_data["Salary"] = "N/A"
                    
                    # Initialize skills and education fields
                    job_data["Skills"] = "N/A"
                    job_data["Education"] = "N/A"
                    job_data["Experience"] = "N/A"
                    job_data["Job Level"] = "N/A"
                    
                    # Click on the job listing to view details
                    try:
                        clickable = job_listing.find_element(By.TAG_NAME, "h2")
                        driver.execute_script("arguments[0].click();", clickable)
                        
                        # Wait for the job details to load
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='viewJobQualificationsContainer']"))
                        )
                        human_like_delay()
                        
                        # Extract skills from qualifications section
                        skills_list = []
                        try:
                            qualifications_container = driver.find_element(By.CSS_SELECTOR, "div[data-testid='viewJobQualificationsContainer']")
                            skill_items = qualifications_container.find_elements(By.CSS_SELECTOR, "span[data-testid='viewJobQualificationItem']")
                            
                            for skill_item in skill_items:
                                skills_list.append(skill_item.text.strip())
                            
                            # Process the skills list to separate education from other skills
                            if skills_list:
                                actual_skills, education_items, experience_items, level_items = extract_education_from_skills(skills_list, job_data["Job Title"])
                                
                                # Update job data with the separated values
                                job_data["Skills"] = ", ".join(actual_skills) if actual_skills else "N/A"
                                job_data["Education"] = ", ".join(education_items) if education_items else "N/A"
                                job_data["Experience"] = ", ".join(experience_items) if experience_items else "N/A"
                                job_data["Job Level"] = ", ".join(level_items) if level_items else "N/A"
                            
                        except NoSuchElementException:
                            print("Could not find qualification items")
                            
                    except Exception as e:
                        print(f"Error viewing job details: {e}")
                    
                    jobs_data.append(job_data)
                    print(f"Successfully scraped: {job_data['Job Title']} at {job_data['Company']}")
                    
                    human_like_delay()
                    
                except StaleElementReferenceException:
                    print("Element became stale, moving to next job")
                    continue
                except Exception as e:
                    print(f"Error processing job: {e}")
                    continue
            
            # Go to the next page if not on the last page
            if page < num_pages:
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, "a[data-testid='pageNumberBlockNext']")
                    driver.execute_script("arguments[0].click();", next_button)
                    print(f"Navigating to page {page + 1}")
                    human_like_delay()
                    # Wait for the new page to load
                    WebDriverWait(driver, 15).until(
                        EC.staleness_of(job_listings[0])
                    )
                except Exception as e:
                    print(f"Error navigating to next page: {e}")
                    break
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        driver.quit()
    
    return jobs_data

def main():
    output_file_stem = 'simplyhired_software_developer'
    url = files_and_sources[output_file_stem]
    num_pages = 25
    
    print(f'This script will attempt to scrape {num_pages} pages of job listings')
    
    jobs_data = scrape_simplyhired_jobs(url, num_pages)
    
    if jobs_data:
        print(f'Scraped {len(jobs_data)} unique jobs')
        save_to_csv(jobs_data, 'data/' + output_file_stem + '.csv')
    else:
        print('No jobs scraped')

if __name__ == "__main__":
    main()
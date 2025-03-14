import csv
import re
import pandas as pd
import numpy as np

def standardize_salary(df):
    df_processed = df.copy()
    
    df_processed['salary_min'] = np.nan
    df_processed['salary_max'] = np.nan
    df_processed['salary_avg'] = np.nan
    df_processed['salary_type'] = ''  # hourly, yearly, monthly
    
    for idx, row in df_processed.iterrows():
        salary = str(row['Salary'])
        
        # Skip missing values
        if salary == 'n/a' or pd.isna(salary):
            continue
        
        # Clean the string (remove source info and quotes)
        salary = re.sub(r'\s*\([^)]*\)', '', salary)
        salary = salary.replace('"', '')
        salary_lowercase = salary.lower()
        
        # Determine salary type
        if 'hour' in salary_lowercase:
            salary_type = 'hourly'
        elif 'month' in salary_lowercase:
            salary_type = 'monthly'
        elif 'year' in salary_lowercase or 'k' in salary_lowercase or 'm' in salary_lowercase:
            # In rare cases, these are actually monthly (e.g. "$4K - $7K"), so will just filter out outliers after
            salary_type = 'yearly'
        else:
            salary_type = 'unknown'
        
        df_processed.at[idx, 'salary_type'] = salary_type
        
        # Extract numerical values
        numbers = re.findall(r'[\d,.]+', salary_lowercase)

        if len(numbers) >= 2:
            # Handle ranges like "$121K - $160K"
            min_val = float(numbers[0].replace(',', '').replace('k', '000').replace('m', '000000'))
            max_val = float(numbers[1].replace(',', '').replace('k', '000').replace('m', '000000'))
            
            # Handle K/M abbreviations if not already done
            if 'k' in salary_lowercase:
                if min_val < 1000:
                    min_val *= 1000
                if max_val < 1000:
                    max_val *= 1000
            elif 'M' in salary:
                if min_val < 1000000:
                    min_val *= 1000000
                if max_val < 1000000:
                    max_val *= 1000000
                
            df_processed.at[idx, 'salary_min'] = min_val
            df_processed.at[idx, 'salary_max'] = max_val
            df_processed.at[idx, 'salary_avg'] = (min_val + max_val) / 2
        elif len(numbers) == 1:
            # Handle single values like "$70K"
            val = float(numbers[0].replace(',', '').replace('K', '000').replace('m', '000000'))
            
            # Handle K/M abbreviations if not already done
            if 'k' in salary_lowercase and val < 1000:
                val *= 1000
            elif 'M' in salary and val < 1000000:
                val *= 1000000
                
            df_processed.at[idx, 'salary_min'] = val
            df_processed.at[idx, 'salary_max'] = val
            df_processed.at[idx, 'salary_avg'] = val
    
    # Standardize all salaries to yearly for consistency
    df_processed['salary_standardized'] = np.nan
    
    for idx, row in df_processed.iterrows():
        if pd.isna(row['salary_avg']):
            continue
            
        if row['salary_type'] == 'hourly':
            # Assuming 40 hours/week, 52 weeks/year...
            yearly = row['salary_avg'] * 40 * 52
        elif row['salary_type'] == 'monthly':
            # 12 months per year
            yearly = row['salary_avg'] * 12
        else:
            yearly = row['salary_avg']
            
        df_processed.at[idx, 'salary_standardized'] = yearly
    
    return df_processed

def standardize_location(df, use_unabbreviated_name=False):
    state_dict = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
        'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
        'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
        'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
        'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
        'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
        'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
        'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
        'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
        'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
        'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
        'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
        'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
    }
    
    df_processed = df.copy()

    df_processed['state'] = ''

    for idx, row in df_processed.iterrows():
        location_lowercase = str(row['Location']).lower()
        # Skip missing values
        if location_lowercase == 'n/a' or pd.isna(location_lowercase):
            continue

        # Check for remote
        if location_lowercase == 'remote':
            df_processed.at[idx, 'state'] = 'Remote'
            continue

        # Check for "United States"
        if location_lowercase == 'united states':
            df_processed.at[idx, 'state'] = 'United States'
            continue

        # Otherwise, check for valid state code
        # (Space at end followed by 2 chars)
        if len(location_lowercase) >= 3 and location_lowercase[-3] == ' ':
            state_code = location_lowercase[-2:].upper()
            if state_code in state_dict:
                if use_unabbreviated_name:
                    df_processed.at[idx, 'state'] = state_dict[state_code]
                else:
                    df_processed.at[idx, 'state'] = state_code
                continue

        # Lastly, check for state full name already in string
        for code, name in state_dict.items():
            if name.lower() in location_lowercase:
                if use_unabbreviated_name:
                    df_processed.at[idx, 'state'] = name
                else:
                    state_code = next((key for key, value in state_dict.items() if value == name), None)
                    df_processed.at[idx, 'state'] = state_code

    return df_processed

def extract_job_title(title):
    """
    Tries to standardize job titles based on regex.
    Assumes title is already lowercase.
    """

    # Software Engineer variations
    if re.search(r'software\s+engineer|swe|engineer,?\s+software', title):
        return 'Software Engineer'
    
    # Computer Scientist variations
    if re.search(r'computer\s+scientist', title):
        return 'Computer Scientist'
    
    # Research Scientist variations (before general researcher)
    if re.search(r'research\s+scientist', title):
        return 'Research Scientist'
    
    # Researcher variations
    if re.search(r'researcher', title):
        return 'Researcher'
    
    # Data Scientist variations
    if re.search(r'data\s+scien(?:ce|tist)|machine\s+learning|ml\s+engineer', title):
        return 'Data Scientist'

    # Misc. Scientist variations (after specific scientist roles)
    if re.search(r'scientist', title):
        return 'Scientist'
    
    # DevOps/SRE variations
    if re.search(r'devops|site\s+reliability|sre|platform\s+engineer|infrastructure', title):
        return 'DevOps/SRE'
    
    # Frontend variations
    if re.search(r'front\s*end|frontend|ui\s+developer|react|angular|vue', title):
        return 'Frontend Developer'
    
    # Backend variations
    if re.search(r'back\s*end|backend|api\s+developer|server', title):
        return 'Backend Developer'
    
    # Full-stack variations
    if re.search(r'full\s*stack|fullstack', title):
        return 'Full Stack Developer'
    
    # QA/Test Engineer variations
    if re.search(r'qa|quality\s+assurance|test\s+engineer|automation\s+engineer', title):
        return 'QA Engineer'
    
    # Mobile Developer variations
    if re.search(r'mobile|ios|android|app\s+developer', title):
        return 'Mobile Developer'
    
    # Product Manager variations
    if re.search(r'product\s+manager|pm,?\s+software', title):
        return 'Product Manager'

    # Software Developer variations
    if re.search(r'software\s+developer|developer,?\s+software', title):
        return 'Software Developer'
    
    # Software/systems architect
    if re.search(r'architect', title):
        return 'Software/Systems Architect'

    # Catch-all for other engineering roles
    if re.search(r'engineer|developer', title):
        return 'Other Engineering'

    # Research assistant
    if re.search(r'research\sassistant', title):
        return 'Research Assistant'

    # Data analyst
    if re.search(r'data\sanalyst', title):
        return 'Data Analyst'

    # Simple check for programmer
    if re.search(r'programmer', title):
        return 'Programmer'
    
    return 'Other'

def standardize_job_title(df):
    """Standardizes both title level from Job Title."""

    df_processed = df.copy()

    df_processed['standardized_title'] = pd.NA

    for idx, row in df_processed.iterrows():
        job_title = row['Job Title']
        if pd.isna(job_title):
            continue

        df_processed.at[idx, 'standardized_title'] = extract_job_title(job_title.lower())

    return df_processed

def extract_education_level(text):
    """Ordinal encoding for education level in Education."""
    if any(term in text for term in ['phd', 'doctoral', 'doctorate', 'ph.d']):
        return 4  # Doctoral level
    elif any(term in text for term in ['master', 'm.s.', 'm.a.']):
        return 3  # Master's level
    elif any(term in text for term in ['bachelor', 'bs', 'b.s.', 'b.a.']):
        return 2  # Bachelor's level
    elif any(term in text for term in ['associate', 'diploma', 'certificate']):
        return 1  # Associate level
    else:
        return pd.NA

def extract_experience_level(text):
    """
    Extract the greatest number mentioned in the text, assuming these refer to years.
    Returns an ordinal encoding based on years of experience:
    1 = 1-2 years
    2 = 3-5 years
    3 = 6-9 years
    4 = 10+ years
    """

    numbers = re.findall(r'\b(\d+)\b', text)
    years = [int(num) for num in numbers if num]
    
    if years == []:
        return pd.NA

    max_years = max(years)
    
    if max_years <= 2:
        return 1  # 1-2 years
    elif max_years <= 5:
        return 2  # 3-5 years
    elif max_years <= 9:
        return 3  # 6-9 years
    else:
        return 4  # 10+ years

def extract_job_level(text):
    """Ordinal encoding for Job Level."""
    if 'junior' in text or 'entry' in text:
        return 1
    elif 'mid' in text:
        return 2
    elif 'senior' in text:
        return 3
    else:
        return pd.NA

def standardize_3_experience_features(df):
    df_processed = df.copy()

    df_processed['education_level'] = pd.NA
    df_processed['experience_level'] = pd.NA
    df_processed['job_level'] = pd.NA

    for idx, row in df_processed.iterrows():
        education = row['Education']
        if pd.notna(education):
            df_processed.at[idx, 'education_level'] = extract_education_level(education.lower())

        experience = row['Experience']
        if pd.notna(experience):
            df_processed.at[idx, 'experience_level'] = extract_experience_level(experience.lower())

        job_level = row['Job Level']
        if pd.notna(job_level):
            df_processed.at[idx, 'job_level'] = extract_job_level(job_level.lower())

    return df_processed

def main():
    stem = 'combined_output'
    df = pd.read_csv(stem + '.csv')
    df_processed = standardize_salary(df)
    df_processed = standardize_location(df_processed)
    df_processed = standardize_job_title(df_processed)
    df_processed = standardize_3_experience_features(df_processed)
    df_processed.to_csv(stem + '_CLEANED.csv', index=False)

if __name__ == "__main__":
    main()

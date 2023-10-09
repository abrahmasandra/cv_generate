from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
import os
from django.conf import settings
import shutil
import zipfile

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from .forms import LinkedInForm

# Create your views here.

def index(request):
    if request.method == "GET":
        form = LinkedInForm()
        return render(request, 'index.html', {"form": form})

def scrape_and_generate_cv(request):
    form = LinkedInForm(request.POST)

    if form.is_valid():
        username = form.cleaned_data['username']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        # Implement the LinkedIn scraping logic and LaTeX template generation here
        # Replace the example_cv_data with the scraped data
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Run Chrome in headless mode (no visible browser window)
        service_object = Service("/usr/local/bin/chromedriver")

        driver = webdriver.Chrome(service=service_object, options=chrome_options)

        driver.get("https://www.linkedin.com/uas/login")
        time.sleep(3)

        _login_linkedin(driver, email, password)

        cv_data = {
            'email': email,
            'username': username,
        }

        try:
            cv_data["work_experiences"] = _extract_work_experiences(driver, username)
        except:
            cv_data["work_experiences"] = []
        
        try:
            cv_data["courses"] = _extract_courses(driver, username)
        except:
            cv_data["courses"] = ""
        
        try:
            cv_data["honors"] = _extract_honors(driver, username)
        except:
            cv_data["honors"] = ""
        
        try:
            cv_data["skills"] = _extract_skills(driver, username)
        except:
            cv_data["skills"] = ""
        
        try:
            cv_data["name"] = _extract_name(driver, username)
        except:
            cv_data["name"] = ""
        
        try:
            cv_data["projects"] = _extract_projects(driver, username)
        except:
            cv_data["projects"] = []
        
        try:
            cv_data["education"] = _extract_latest_education(driver, username)
        except:
            cv_data["education"] = {
                'university': "UNIVERSITY",
                'degree': 'DEGREE',
                'duration': 'DURATION'
            }

        # Pass the scraped data to the template
        # return render(request, 'cv_template.tex', {'data': example_cv_data})

        # Generate the LaTeX content using the cv_template.tex template
        latex_content = render_to_string('cv_template.tex', {'data': cv_data})
        
        # Create temporary directory to hold the files
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_cv')
        os.makedirs(temp_dir, exist_ok=True)

        # Create temporary files for PDF and TEX
        temp_pdf_file = os.path.join(settings.MEDIA_ROOT, 'temp_cv.pdf')
        temp_tex_file = os.path.join(settings.MEDIA_ROOT, 'temp_cv.tex')

        # Write the LaTeX content to the TEX file
        with open(temp_tex_file, 'w') as tex_file:
            tex_file.write(latex_content)

        # Use subprocess to call pdflatex to generate the PDF from the TEX file
        # Make sure pdflatex is installed on your system
        import subprocess
        subprocess.run(['pdflatex', '--output-directory', settings.MEDIA_ROOT, temp_tex_file])

        # Create a zip file containing the generated PDF and TEX files
        zip_file_path = os.path.join(settings.MEDIA_ROOT, 'generated_cv.zip')
        with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
            zip_file.write(temp_pdf_file, os.path.basename(temp_pdf_file))
            zip_file.write(temp_tex_file, os.path.basename(temp_tex_file))
        
        # Read the content of the zip file
        with open(zip_file_path, 'rb') as zip_file:
            zip_content = zip_file.read()

        # Clean up the temporary files
        os.remove(temp_tex_file)
        os.remove(temp_pdf_file)
        os.rmdir(temp_dir)

        # Create the HTTP response with the PDF content for download
        response = HttpResponse(zip_content, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="generated_cv.zip"'
        return response

def _login_linkedin(driver, EMAIL, PASSWORD):
        email = driver.find_element(By.ID,"username")
        email.send_keys(EMAIL)
        password = driver.find_element(By.ID,"password")
        password.send_keys(PASSWORD)

        time.sleep(3)
        password.send_keys(Keys.RETURN)

def _extract_work_experiences(driver, USERNAME):
    # Send an HTTP GET request to the LinkedIn experiences page
    driver.get(f"https://www.linkedin.com/in/{USERNAME}/details/experience/")
    time.sleep(3)

    # Find the section that contains work experiences
    work_experiences_section = driver.find_element(By.CLASS_NAME, "pvs-list__container")

    # Initialize an empty list to store work experiences
    work_experiences = []

    # Iterate through each work experience entry
    work_entries = work_experiences_section.find_elements(By.CLASS_NAME, "artdeco-list__item")

    for work_entry in work_entries:
        # Extract the relevant information from the elements
        place = work_entry.find_element(By.CLASS_NAME, "justify-space-between")
        data = place.find_elements(By.CSS_SELECTOR,"span[aria-hidden]")

        data = [d.text for d in data]
        # create a dictionary to store the extracted data
        work_experience = {}
        work_experience["title"] = data[0]
        work_experience["company"] = data[1].split("·")[0].strip()
        work_experience["duration"] = data[2].split("·")[0].strip()

        if len(data) > 3:
            work_experience["location"] = data[3].split("·")[0].strip()
        else:
            work_experience["location"] = "LOCATION"

        try:
            description = work_entry.find_element(By.CSS_SELECTOR, ".pvs-list__outer-container span[aria-hidden]")
            work_experience["description"] = description.text.split('\n\n')
        except:
            work_experience["description"] = []

        work_experiences.append(work_experience)
    
    return work_experiences

def _extract_courses(driver, USERNAME):
    # Send an HTTP GET request to the LinkedIn courses page
    driver.get(f"https://www.linkedin.com/in/{USERNAME}/details/courses/")
    time.sleep(3)

    # Find the section that contains courses
    courses_section = driver.find_element(By.CSS_SELECTOR, ".pvs-list")

    # Initialize an empty list to store courses
    courses = courses_section.find_elements(By.CSS_SELECTOR, ".t-bold span[aria-hidden]")
    courses = [course.text for course in courses]

    return " - ".join(courses)    

def _extract_honors(driver, USERNAME):
    # Send an HTTP GET request to the LinkedIn courses page
    driver.get(f"https://www.linkedin.com/in/{USERNAME}/details/honors/")
    time.sleep(3)

    # Find the section that contains courses
    honors_section = driver.find_element(By.CSS_SELECTOR, ".pvs-list")

    # Initialize an empty list to store courses
    honors = honors_section.find_elements(By.CSS_SELECTOR, ".t-bold span[aria-hidden]")
    honors = [honor.text for honor in honors]

    return " - ".join(honors)

def _extract_skills(driver, USERNAME):
    # Send an HTTP GET request to the LinkedIn courses page
    driver.get(f"https://www.linkedin.com/in/{USERNAME}/details/skills/")
    time.sleep(3)

    # Find the section that contains courses
    skills_section = driver.find_element(By.CSS_SELECTOR, ".pvs-list")

    # Initialize an empty list to store courses
    skills = skills_section.find_elements(By.CSS_SELECTOR, ".t-bold span[aria-hidden]")
    skills = [skill.text for skill in skills]

    return " - ".join(skills)

def _extract_name(driver, USERNAME):
    # Send an HTTP GET request to the LinkedIn home page
    driver.get(f"https://www.linkedin.com/in/{USERNAME}/")
    time.sleep(3)

    # Find the section that contains courses
    name_section = driver.find_element(By.CSS_SELECTOR, ".ph5")

    # Initialize an empty list to store courses
    name = name_section.find_element(By.CSS_SELECTOR, "h1").text
    return name

def _extract_projects(driver, USERNAME):
    # Send an HTTP GET request to the LinkedIn projects page
    driver.get(f"https://www.linkedin.com/in/{USERNAME}/details/projects")
    time.sleep(3)

    # Find the section that contains projects
    proj_section = driver.find_element(By.CSS_SELECTOR, ".pvs-list__container")

    # Initialize an empty list to store projects
    projects = []

    project_entries = proj_section.find_elements(By.CSS_SELECTOR, ".artdeco-list__item")
    
    for proj_entry in project_entries:
        # Extract the relevant information from the elements
        heading = proj_entry.find_element(By.CLASS_NAME, "justify-space-between")
        data = heading.find_elements(By.CSS_SELECTOR,"span[aria-hidden]")

        description = proj_entry.find_elements(By.CSS_SELECTOR, ".pvs-list__outer-container .pvs-list__outer-container span[aria-hidden]")

        data.extend(description)
        data = [d.text for d in data]

        # create a dictionary to store the extracted data
        project = {}
        project["title"] = data[0]
        project["duration"] = data[1]
        project["description"] = data[2].split('\n\n')

        projects.append(project)
    
    return projects

def _extract_latest_education(driver, USERNAME):
    # Send an HTTP GET request to the LinkedIn education page
    driver.get(f"https://www.linkedin.com/in/{USERNAME}/details/education")
    time.sleep(3)

    # Find the section that contains education
    edu_section = driver.find_element(By.CSS_SELECTOR, ".pvs-list")
    heading_latest = edu_section.find_element(By.CLASS_NAME, "justify-space-between")

    data = heading_latest.find_elements(By.CSS_SELECTOR,"span[aria-hidden]")
    data = [d.text for d in data]

    education = {}

    if len(data) == 2:
        education["university"] = data[0]
        education["duration"] = data[1]
        education["degree"] = "DEGREE"
    else:
        education["university"] = data[0]
        education["degree"] = data[1]
        education["duration"] = data[2]

    return education
import re
import json
from pathlib import Path
from datetime import datetime

from pypdf import PdfReader

from src.preprocessing import clean_text


# Path to skills.json
SKILLS_FILE = (
    Path(__file__).resolve().parent.parent
    / "resources"
    / "skills.json"
)


def load_skills():
    """Load skills from the JSON file."""
    with open(SKILLS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


SKILLS = load_skills()


def extract_text_from_pdf(pdf_path):
    """Extract and clean text from a resume PDF."""
    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return clean_text(text)


def extract_skills(text):
    """Extract known skills from resume text."""
    found_skills = []

    text = text.lower()

    for skill in SKILLS:
        pattern = r"(?<!\w)" + re.escape(skill.lower()) + r"(?!\w)"

        if re.search(pattern, text):
            found_skills.append(skill)

    return found_skills


def extract_experience(text):
    """Extract total professional experience in years."""

    experience_section = text

    # Start from Professional Experience section
    if "professional experience" in experience_section:
        experience_section = experience_section.split(
            "professional experience", 1
        )[1]

    # Stop before sections that should not be counted
    for section in [
        "research experience",
        "publications and patents",
        "projects",
        "teaching experience",
        "courses",
        "skills",
        "scholastic achievements",
        "positions of responsibility",
        "extra curricular activities",
        "education",
    ]:
        if section in experience_section:
            experience_section = experience_section.split(
                section, 1
            )[0]

    # Month names and abbreviations
    month_pattern = (
        r"(?:january|february|march|april|may|june|july|august|"
        r"september|october|november|december|"
        r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)"
    )

    # Example matches:
    # Dec 2022 Present
    # Aug 2020 Nov 2022
    # May 2019 July 2019
    date_pattern = (
        rf"\b({month_pattern})\s+(19\d{{2}}|20\d{{2}})"
        rf"\s+"
        rf"(present|current|{month_pattern}\s+(19\d{{2}}|20\d{{2}}))\b"
    )

    matches = re.findall(
        date_pattern,
        experience_section,
        re.IGNORECASE
    )

    # Month lookup table
    month_number = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "sept": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    }

    total_months = 0

    for match in matches:
        start_month = match[0].lower()
        start_year = int(match[1])
        end = match[2]

        # Convert starting date to months
        start_value = (
            start_year * 12
            + month_number[start_month]
        )

        # Handle Present / Current
        if end.lower() in ["present", "current"]:
            now = datetime.now()

            end_value = (
                now.year * 12
                + now.month
            )

        else:
            # Example: "nov 2022"
            end_parts = end.split()

            end_month = end_parts[0].lower()
            end_year = int(end_parts[1])

            end_value = (
                end_year * 12
                + month_number[end_month]
            )

        total_months += end_value - start_value

    # Convert months to years
    return round(total_months / 12, 1)

EDUCATION_FILE = (
    Path(__file__).resolve().parent.parent
    / "resources"
    / "education.json"
)


def load_education():
    with open(EDUCATION_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


EDUCATION = load_education()

def extract_education(text):
    """Extract degree and field of study from resume text."""

    education_text = text.lower()

    # Fix common PDF extraction problems
    education_text = education_text.replace(
        "t echnology",
        "technology"
    )

    education_text = education_text.replace(
        "e ngineering",
        "engineering"
    )

    degree = ""

    for degree_name, aliases in EDUCATION["degrees"].items():
        for alias in aliases:
            if alias in education_text:
                degree = degree_name
                break

        if degree:
            break

    field = ""

    for field_name in EDUCATION["fields"]:
        if field_name in education_text:
            field = field_name
            break

    return degree, field


def process_resume(pdf_path):
    """Process a complete resume and return structured data."""

    text = extract_text_from_pdf(pdf_path)

    skills = extract_skills(text)

    experience = extract_experience(text)

    degree, field = extract_education(text)

    resume_data = {
        "text": text,
        "skills": skills,
        "experience": experience,
        "degree": degree,
        "field": field,
    }

    return resume_data
import requests
import json
import time
from bs4 import BeautifulSoup
import argparse
import sys


# Wikipedia base API URL
WIKI_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"

# Wikipedia base URL to scrape the full page
WIKI_PAGE_URL = "https://en.wikipedia.org/wiki/"


# Function to get disorder description from Wikipedia's API
def get_disorder_info(disorder_name):
    disorder_info_url = WIKI_API_URL + disorder_name
    try:
        response = requests.get(disorder_info_url)
        if response.status_code == 200:
            return response.json()
            print(response.json())
    except Exception as e:
        print(f"Error fetching data for {disorder_name}: {e}")
    return {}


# Function to get disorder full content by scraping Wikipedia
def scrape_wikipedia_content(disorder_name):
    disorder_url = WIKI_PAGE_URL + disorder_name
    print(disorder_url)
    try:
        response = requests.get(disorder_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract the main content of the Wikipedia page
            content_div = soup.find('div', {'class': 'mw-parser-output'})
            
            # Collect all the paragraphs as text
            paragraphs = content_div.find_all('p')
            full_text = "\n".join([para.get_text() for para in paragraphs if para.get_text().strip()])

            return full_text
        else:
            print(f"Failed to fetch data for {disorder_name}, status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching content for {disorder_name}: {e}")
    return ""


def update_json_with_scraped_content(input_filename, output_filename):
    # Load the existing JSON data
    with open(input_filename, 'r', encoding='utf-8') as f:
        disorders_data = json.load(f)

     # Loop over each disorder and update the content
    for disorder in disorders_data:
        disorder_name = disorder["link"].split("/wiki/")[1]  # Extract the Wikipedia page title from the link
        print(f"Fetching full content for: {disorder['name']} ({disorder_name})")

        # Scrape the full content from Wikipedia
        full_content = scrape_wikipedia_content(disorder_name)
        print(f"Full content fetched for: {disorder['name']} ({disorder_name})")
        print(full_content)

        # Update the "content" field with the full content
        disorder["content"] = full_content

        # Description from Wikipedia's API
        disorder_info = get_disorder_info(disorder_name)

        # Update the "description" field with the API content
        disorder["description"] = disorder_info.get("extract", "")

        time.sleep(0.1)  # Wait 0.1 second between requests to avoid overwhelming Wikipedia's servers

    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(disorders_data, f, ensure_ascii=False, indent=4)

    print(f"Updated JSON file saved as: {output_filename}")


def description_and_content(input_filename, output_filename):
    update_json_with_scraped_content(input_filename, output_filename) # Fill Merged Json File

##### Mode 2 #####

# Function to scrape the Wikipedia page and extract specific sections based on <h2> tags
def scrape_disorder_sections(disorder_name):
    disorder_url = WIKI_PAGE_URL + disorder_name
    print(disorder_url)
    try:
        response = requests.get(disorder_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract the main content of the Wikipedia page
            content_div = soup.find('div', {'class': 'mw-parser-output'})
            
            # Prepare a dictionary to store sections
            sections = {
                "causes": "",
                "symptoms": "",
                "treatment": "",
                "diagnosis": "",
                "prevention": "",
                "epidemiology": ""
            }

            # Keywords to identify sections based on <h2> tags
            keywords = {
                "causes": ["Causes"],
                "symptoms": ["Signs and symptoms", "Symptoms", "Signs and Symptoms", "Signs" ,"signs and symptoms"],
                "treatment": ["Treatment", "Management"],
                "diagnosis": ["Diagnosis", "Diagnostic criteria"],
                "prevention": ["Prevention", "Control", "Help"],
                "epidemiology": ["Epidemiology"]
            }
            
            # Flag to track which section we're currently in
            current_section = None
            section_content = ""

            # Iterate through the tags to find relevant <h2> sections
            for tag in content_div.find_all(['h2', 'h3', 'p', 'ul']):
                if tag.name == 'h2':
                    # Check if the header matches any of the keywords to identify sections
                    header_text = tag.get_text().strip()
                    print(header_text)
                    current_section = None
                    for section, terms in keywords.items():
                        if any(term in header_text for term in terms):
                            print(f"Found section: {section}")
                            current_section = section
                            section_content = ""
                            break
                elif tag.name in ['p', 'ul'] and current_section:
                    # Append the content to the current section until the next <h2> is found
                    section_content += tag.get_text() + "\n"
                    sections[current_section] = section_content.strip()
                    print(section_content)

            return sections
        else:
            print(f"Failed to fetch data for {disorder_name}, status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching content for {disorder_name}: {e}")
    return {}

# Function to update JSON with detailed sections from scraped Wikipedia content
def update_json_with_sections(input_filename, output_filename):
    # Load the existing JSON data
    with open(input_filename, 'r', encoding='utf-8') as f:
        disorders_data = json.load(f)

    # Loop over each disorder and update it with the sectioned content
    for disorder in disorders_data:
        disorder_name = disorder["link"].split("/wiki/")[1]  # Extract the Wikipedia page title from the link
        print(f"Fetching detailed sections for: {disorder['name']} ({disorder_name})")

        # Scrape the specific sections from Wikipedia
        sections = scrape_disorder_sections(disorder_name)
        print(f"Sections fetched for: {disorder['name']} ({disorder_name})")

        # Update the JSON structure with the relevant sections
        disorder["causes"] = sections.get("causes", "")
        disorder["symptoms"] = sections.get("symptoms", "")
        disorder["treatment"] = sections.get("treatment", "")
        disorder["diagnosis"] = sections.get("diagnosis", "")
        disorder["prevention"] = sections.get("prevention", "")
        disorder["epidemiology"] = sections.get("epidemiology", "")

        # Optional: You can add a short delay between requests
        time.sleep(0.1)  # Wait 0.1 second between requests to avoid overwhelming Wikipedia's servers

    # Save the updated JSON data
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(disorders_data, f, ensure_ascii=False, indent=4)

    print(f"Updated JSON file saved as: {output_filename}")



def main(mode):
    if mode == 1:
        input_json_file = 'merged_disorders.json'
        output_filename = 'merged_disorders_FILLED.json'
        description_and_content(input_json_file, output_filename)
    elif mode == 2:
        input_json_file = 'merged_disorders_FILLED.json'
        output_filename = 'merged_disorders_FILLED_WITH_SECTIONS1.json'
        update_json_with_sections(input_json_file, output_filename)
    else:
        print("Invalid mode selected. Use --help for more information.")

if __name__ == "__main__":
    modes = {
        1: "Fill content and description of a JSON list of disorders.",
        2: "Associate new information to a JSON list of disorders."
    }
    
    parser = argparse.ArgumentParser(description="Mental disorders gathering data.")
    parser.add_argument('mode', type=int, choices=modes.keys(), nargs='?', help='Options: ' + ', \n'.join([f"{k} - {v}" for k, v in modes.items()]))
    
    args = parser.parse_args()
    
    if args.mode is None:
        parser.print_help()
        sys.exit(1)
    
    main(args.mode)


# # # Document

# I want you to web scrap the wikipedia website to create and fill a Json file with the following structure:: Its important
# to you to access the like of each entry and find the type of header of the thing I want you to find like for example: this one
# <h2 id="Signs_and_symptoms">Signs and symptoms</h2> so you can know that the content is about the symptoms of the disease. and you extract the text
# next to it. its important you to use some keywords so you can have more accuracy in the extraction of each item, for example in "Signs and symptoms" could be like 
# "Signs and symptoms" or "Signs" or "Symptoms" or more, and the same thing for the other items.

# For the code I provided, I want you to associate that task with the mode 2, you can create new funtions for it

# Name:
# # Type:
# # Description:
# # Link: 
# # Content (bigger description):
# # Causes: (optional/empty)
# # Symptoms:(optional/empty)
# # Treatment: (optional/empty)
# # Diagnosis: (optional/empty)
# # Prevention: (optional/empty)
# # Epidemiology: (optional/empty)

# # # Input
# [
#     {
#         "name": "Agoraphobia",
#         "type": "Anxiety disorders",
#         "link": "https://en.wikipedia.org/wiki/Agoraphobia",
#         "description": "\n\nAgoraphobia is a mental and behavioral disorder, specifically an anxiety disorder characterized by symptoms of anxiety in situations where the person perceives their environment to be unsafe with no easy way to escape. These situations can include public transit, shopping centers, crowds and queues, or simply being outside their home on their own. Being in these situations may result in a panic attack. Those affected will go to great lengths to avoid these situations. In severe cases, people may become completely unable to leave their homes.",
#         "content": "\nAgoraphobia[1] is a mental and behavioral disorder,[5]  ......."
#     ...
# ]
# # # Output
# [
#     {
#         "name": "Agoraphobia",
#         "type": "Anxiety disorders",
#         "link": "https://en.wikipedia.org/wiki/Agoraphobia",
#         "description": "\n\nAgoraphobia is a mental and behavioral disorder, specifically an anxiety disorder characterized by symptoms of anxiety in situations where the person perceives their environment to be unsafe with no easy way to escape. These situations can include public transit, shopping centers, crowds and queues, or simply being outside their home on their own. Being in these situations may result in a panic attack. Those affected will go to great lengths to avoid these situations. In severe cases, people may become completely unable to leave their homes.",
#         "content": "\nAgoraphobia[1] is a mental and behavioral disorder,[5]  ......."
#         "causes": "",
#         "symptoms": "",
#         "treatment": "",
#         "diagnosis": "",
#         "prevention": "",
#         "epidemiology": "",
#     }
# ]


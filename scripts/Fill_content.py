import requests
import json
import time
from bs4 import BeautifulSoup
import argparse
import sys
import re


# Wikipedia base API URL
WIKI_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"

# Wikipedia base URL to scrape the full page
WIKI_PAGE_URL = "https://en.wikipedia.org/wiki/"

WIKI_DATA_BASE_URL = "https://www.wikidata.org/wiki/"
WIKI_DATA_BASE_URL_JSON = "https://www.wikidata.org/wiki/Special:EntityData/"

# Function to get disorder description from Wikipedia's API
def get_disorder_info(disorder_name):
    disorder_info_url = WIKI_API_URL + disorder_name
    try:
        response = requests.get(disorder_info_url)
        if response.status_code == 200:
            return response.json()
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
    failed_attempts = 0
    while True:
        try:
            response = requests.get(disorder_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract the main content of the Wikipedia page
                content_div = soup.find('div', {'class': 'mw-content-ltr mw-parser-output'})

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
                    "symptoms": ["Signs and symptoms", "Symptoms", "Signs and Symptoms", "Signs", "signs and symptoms"],
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
                        print(f"H2:--{tag.name}--{header_text}")
                        current_section = None
                        for section, terms in keywords.items():
                            if any(term in header_text for term in terms):
                                print(f"FOUND_SECTION:--- {section}")
                                current_section = section
                                section_content = ""
                                break
                    elif tag.name in ['p', 'ul', 'h3'] and current_section:
                        # Append the content to the current section until the next <h2> is found
                        section_content += tag.get_text() + "\n"
                        sections[current_section] = section_content.strip()
                        print(f"SECTION ADDED---{section_content}")
                    else:
                        print(f"ELSE:---{tag.name}---{tag.get_text()}")
                        print("-----------------------------------------------")
                return sections
            else:
                print(f"Failed to fetch data for {disorder_name}, status code: {response.status_code}")
                print("-----------------------------------------------")
                failed_attempts += 1
                if failed_attempts > 5:
                    break
                time.sleep(1)
        except Exception as e:
            print(f"Error fetching content for {disorder_name}: {e}")
            failed_attempts += 1
            if failed_attempts > 5:
                break
            time.sleep(1)
    return ""


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
        time.sleep(0.05)  # Wait 0.1 second between requests to avoid overwhelming Wikipedia's servers

    # Save the updated JSON data
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(disorders_data, f, ensure_ascii=False, indent=4)

    print(f"Updated JSON file saved as: {output_filename}")

##### Mode 3  #####


def get_WikiBase(disorder_name):
    disorder_info = get_disorder_info(disorder_name)
    return disorder_info.get("wikibase_item", "")

def get_Revisions(disorder_name):
    number_of_revisions = 0
    number_of_revisions = get_disorder_info(disorder_name)
    return number_of_revisions.get("revision", "")

def addWikiDataLink(input_filename, output_filename):
    # Load the existing JSON data
    with open(input_filename, 'r', encoding='utf-8') as f:
        disorders_data = json.load(f)

    # Loop over each disorder and update the content
    for disorder in disorders_data:
        disorder_name = disorder["link"].split("/wiki/")[1]
        print(f"Fetching Wikidata link for: {disorder['name']} ({disorder_name})")

        id = get_WikiBase(disorder_name)

        print(f"WikiBase ID fetched for: {disorder['name']} ({disorder_name}): {id}")

        url_wikidata = WIKI_DATA_BASE_URL + id
        url_wikidataJson = WIKI_DATA_BASE_URL_JSON + id + ".json"
        number_of_revisions = get_Revisions(disorder_name)

        disorder["wikidata_id"] = id
        disorder["wikidata_url"] = url_wikidata
        disorder["wikidata_url_json"] = url_wikidataJson
        disorder["number_of_revisions"] = number_of_revisions

        time.sleep(0.05)

    # Save the updated JSON data
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(disorders_data, f, ensure_ascii=False, indent=4)

    print(f"Updated JSON file saved as: {output_filename}")


##### Mode 4 #####
def edit_content(input_filename, output_filename):
    # Load the existing JSON data
    with open(input_filename, 'r', encoding='utf-8') as f:
        disorders_data = json.load(f)

    # Loop over each disorder and update the content
    for disorder in disorders_data:
        disorder_name = disorder["link"].split("/wiki/")[1]  # Extract the Wikipedia page title from the link
        print(f"Fetching full content for: {disorder['name']} ({disorder_name})")

        # Scrape the full content from Wikipedia
        full_content = selective_scrape_wikipedia_content(disorder_name)
        print(f"Full content fetched for: {disorder['name']} ({disorder_name})")
        print(full_content)

        # Update the "content" field with the full content
        disorder["content"] = full_content

        time.sleep(0.05)  # Wait 0.1 second between requests to avoid overwhelming Wikipedia's servers

    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(disorders_data, f, ensure_ascii=False, indent=4)


    print(f"Updated JSON file saved as: {output_filename}")


def selective_scrape_wikipedia_content(disorder_name):
    disorder_url = WIKI_PAGE_URL + disorder_name
    print(disorder_url)
    failed_attempts = 0
    while True:
        try:
            response = requests.get(disorder_url)
            if response.status_code == 200:
                print("RESPONSE 200")
                soup = BeautifulSoup(response.content, 'html.parser')
                #print(f"SOUP---{soup}")

                # Extract the main content of the Wikipedia page
                content_div = soup.find('div', {'class': 'mw-content-ltr mw-parser-output'})
                keywords = {
                    "causes": ["Causes"],
                    "symptoms": ["Signs and symptoms", "Symptoms", "Signs and Symptoms", "Signs", "signs and symptoms"],
                    "treatment": ["Treatment", "Management"],
                    "diagnosis": ["Diagnosis", "Diagnostic criteria"],
                    "prevention": ["Prevention", "Control", "Help"],
                    "epidemiology": ["Epidemiology"]
                }

                # Collect all the paragraphs as text except if the paragraphs belong to a h2 and behind
                # from the keywords provided

                full_text = ""

                # Flag to track if we are in a relevant section
                in_relevant_section = False


                # Iterate through the tags to find relevant <h2> sections
                for tag in content_div.find_all(['h2', 'h3', 'p', 'ul']):
                    if tag.name == 'h2':
                        # Check if the header matches any of the keywords to identify sections
                        header_text = tag.get_text().strip()
                        print(f"H2:--{tag.name}--{header_text}")
                        print("-----------------------------------------------")
                        in_relevant_section = False
                        for section, terms in keywords.items():
                            if any(term in header_text for term in terms):
                                print(f"IRRELEVANT_SECTION:---{section}")
                                print("-----------------------------------------------")
                                in_relevant_section = True
                                break
                        full_text += tag.get_text() + "\n"
                    elif tag.name in ['p', 'ul', 'h3'] and not in_relevant_section:
                        # Append the content to the full text if not in a relevant section
                        full_text += tag.get_text() + "\n"
                        print(f"P_or_UL:---{tag.name}---{tag.get_text()}")
                        print("-----------------------------------------------")
                    else:
                        print(f"ELSE:---{tag.name}---{tag.get_text()}")
                        print("-----------------------------------------------")
                return full_text.strip()
            else:
                print(f"Failed to fetch data for {disorder_name}, status code: {response.status_code}")
                print("-----------------------------------------------")
                failed_attempts += 1
                if failed_attempts > 5:
                    break
                time.sleep(1)
        except Exception as e:
            print(f"Error fetching content for {disorder_name}: {e}")
            failed_attempts += 1
            if failed_attempts > 5:
                break
            time.sleep(1)
    return ""

##### Mode 5 #####
def get_infobox(url):
    failed_attempts = 0
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                bs = BeautifulSoup(response.text, 'html.parser')

                table = bs.find('table', {'class' :'infobox'})

                if not table:
                    return None

                result = {}

                for row in table.find_all('tr'):
                    header = row.find('th', {'class': 'infobox-label'})
                    data = row.find('td', {'class': 'infobox-data'})
                    if header and data:
                        header_text = header.get_text(strip=True)
                        print(f"HEADER: {header_text}")
                        data_text = data.get_text(separator=' ', strip=True)
                        print(f"        DATA: {data_text}")
                        result[header_text] = data_text
                return result
            else:
                print(f"Failed to fetch data for {url}, status code: {response.status_code}")
                print("-----------------------------------------------")
                failed_attempts += 1
                if failed_attempts > 5:
                    break
                time.sleep(1)
        except Exception as e:
            print(f"Error fetching content for {url}: {e}")
            failed_attempts += 1
            if failed_attempts > 5:
                break
            time.sleep(1)
    return ""

def addInfobox(input_filename, output_filename):
    # Load the existing JSON data
    with open(input_filename, 'r', encoding='utf-8') as f:
        disorders_data = json.load(f)

    # Loop over each disorder and update the content
    for disorder in disorders_data:
        disorder_name = disorder["link"].split("/wiki/")[1]  # Extract the Wikipedia page title from the link
        print(f"Fetching infobox for: {disorder['name']} ({disorder_name})")

        # Scrape the infobox from Wikipedia
        infobox = get_infobox(WIKI_PAGE_URL + disorder_name)
        print(f"Infobox fetched for: {disorder['name']} ({disorder_name})")

        # Update the JSON structure with the relevant infobox
        disorder["infobox"] = infobox

        # Optional: You can add a short delay between requests
        time.sleep(0.05)  # Wait 0.1 second between requests to avoid overwhelming Wikipedia's servers

    # Save the updated JSON data
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(disorders_data, f, ensure_ascii=False, indent=4)

    print(f"Updated JSON file saved as: {output_filename}")

##### Mode 6 #####


def get_number_of_edits(url):
    table = get_specific_table(url, 'Edit_history')
    edits_row = table.find('tr', {'id': 'mw-pageinfo-edits'})
    if not edits_row:
        return 0
    edits = edits_row.find_all('td')[1].get_text(strip=True)
    return int(edits.replace(',', ''))


def get_page_views(url):
    failed_attempts = 0
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                table = soup.find('table', {'class': 'wikitable mw-page-info'})

                if not table:
                    raise Exception("Table with class 'wikitable mw-page-info' not found")

                views_row = table.find('tr', {'id': 'mw-pvi-month-count'})
                if not views_row:
                    raise Exception("Row with id 'mw-pvi-month-count' not found")

                views = views_row.find_all('td')[1].get_text(strip=True)
                return int(views.replace(',', ''))
            else:
                print(f"Failed to fetch data for {url}, status code: {response.status_code}")
                print("-----------------------------------------------")
                failed_attempts += 1
                if failed_attempts > 5:
                    break
                time.sleep(1)
        except Exception as e:
            print(f"Error fetching content for {url}: {e}")
            failed_attempts += 1
            if failed_attempts > 5:
                break
            time.sleep(1)
    return 0


def get_specific_table(url, header_id):
    failed_attempts = 0
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                header = soup.find('h2', {'id': header_id})

                if not header:
                    raise Exception(f"Header with id '{header_id}' not found")

                table = header.find_next('table', {'class': 'wikitable mw-page-info'})

                if not table:
                    raise Exception("Table with class 'wikitable mw-page-info' not found after the specified header")

                return table
            else:
                print(f"Failed to fetch data for {url}, status code: {response.status_code}")
                failed_attempts += 1
                if failed_attempts > 5:
                    break
                time.sleep(1)
        except Exception as e:
            print(f"Error fetching content for {url}: {e}")
            failed_attempts += 1
            if failed_attempts > 5:
                break
            time.sleep(1)
    return None


def add_views_and_edits(input_filename, output_filename):
    # Load the existing JSON data
    with open(input_filename, 'r', encoding='utf-8') as f:
        disorders_data = json.load(f)

    # Loop over each disorder and update the content
    for disorder in disorders_data:
        disorder_name = disorder["link"].split("/wiki/")[1]  # Extract the Wikipedia page title from the link
        print(f"Fetching views and edits for: {disorder['name']} ({disorder_name})")

        # Scrape the number of edits from Wikipedia
        edits = get_number_of_edits(WIKI_PAGE_URL + disorder_name + '?action=info#Basic_information')
        print(f"Number of edits fetched for: {disorder['name']} ({disorder_name}): {edits}")

        # Scrape the page views from Wikipedia
        views = get_page_views(WIKI_PAGE_URL + disorder_name + '?action=info#Basic_information')
        print(f"Page views fetched for: {disorder['name']} ({disorder_name}): {views}")

        # Update the JSON structure with the relevant data
        disorder["number_of_edits"] = edits
        disorder["page_views"] = views

        # Optional: You can add a short delay between requests
        time.sleep(0.05)  # Wait 0.1 second between requests to avoid overwhelming Wikipedia's servers

    # Save the updated JSON data
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(disorders_data, f, ensure_ascii=False, indent=4)

    print(f"Updated JSON file saved as: {output_filename}")


##### Mode 7 #####
def clean_text(text):
    # Use regex to remove patterns like [1], [ 408 ], [ 12 ], etc.
    cleaned_text = re.sub(r'\[\s*\d+\s*\]', '', text)
    return cleaned_text.strip()


def clean_json_fields(input_filename, output_filename):
    # Load the existing JSON data
    with open(input_filename, 'r', encoding='utf-8') as f:
        disorders_data = json.load(f)

    # Loop over each disorder and clean the relevant fields
    for disorder in disorders_data:
        for field in ["content", "causes", "symptoms", "treatment", "diagnosis", "prevention", "epidemiology", "infobox"]:
            if field in disorder and isinstance(disorder[field], str):
                disorder[field] = clean_text(disorder[field])

    # Save the cleaned JSON data
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(disorders_data, f, ensure_ascii=False, indent=4)

    print(f"Cleaned JSON file saved as: {output_filename}")


def main(mode):
    if mode == 1:
        input_json_file = 'merged_disorders.json'
        output_filename = 'merged_disorders_FILLED.json'
        description_and_content(input_json_file, output_filename)
    elif mode == 2:
        input_json_file = '/home/francisco/Desktop/MEIC_1YEAR/pri/Mental_Disorders_SearchEngine/data/merged_disorders_FILLED_WITH_PARTIAL_CONTENT.json'
        output_filename = '/home/francisco/Desktop/MEIC_1YEAR/pri/Mental_Disorders_SearchEngine/data/disorders_all_sections_fixed.json'
        update_json_with_sections(input_json_file, output_filename)
    elif mode == 3:
        input_json_file = 'data/merged_disorders_FILLED_WITH_SECTIONS1.json'
        output_filename = 'data/merged_disorders_FILLED_WITH_WIKIDATA_link.json'
        addWikiDataLink(input_json_file, output_filename)
    elif mode == 4:
        input_json_file = 'data/merged_disorders_FILLED_WITH_WIKIDATA_link.json'
        output_filename = 'data/merged_disorders_FILLED_WITH_PARTIAL_CONTENT.json'
        edit_content(input_json_file, output_filename)
    elif mode == 5:
        input_json_file = 'data/disorders_all_sections_fixed.json'
        output_filename = 'data/disorders_plus_infobox.json'
        addInfobox(input_json_file, output_filename)
    elif mode == 6:
        input_json_file = 'data/disorders_plus_infobox.json'
        output_filename = 'data/disorders_views_plus_edits.json'
        add_views_and_edits(input_json_file, output_filename)
    elif mode == 7:
        input_json_file = 'data/disorders_views_plus_edits.json'
        output_filename = 'data/disorders_cleaned_final.json'
        clean_json_fields(input_json_file, output_filename)
    else:
        print("Invalid mode selected. Use --help for more information.")




if __name__ == "__main__":
    modes = {
        1: "Fill content and description of a JSON list of disorders.",
        2: "Associate new information to a JSON list of disorders.",
        3: "Associate Wikidata link to a JSON list of disorders and get the number of revisions.",
        4: "Edit the content, scrape again the wikipedia, but this time select only a part of content",
        5: "Add the infobox (Scrape from Wikipedia) as a new field containing the infobox data in JSON format.",
        6: "Add the wikipedia number of edits and page views over the last 30 days to the JSON",
        7: "Remove redundant text from text fields, example [1], [2], [ 1 ], etc."
    }

    parser = argparse.ArgumentParser(
        description="Mental disorders gathering data.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'mode',
        type=int,
        choices=modes.keys(),
        nargs='?',
        help='Options:\n' + '\n'.join([f"{k} - {v}" for k, v in modes.items()])
    )
    
    args = parser.parse_args()
    
    if args.mode is None:
        #main(4)
        parser.print_help()
        sys.exit(1)
    
    main(args.mode)

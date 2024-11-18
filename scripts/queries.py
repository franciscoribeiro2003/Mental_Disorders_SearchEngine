import requests
import json
import argparse

queries = [
    "Cognitive speed",
    "Triggered by childhood trauma",
    "CBT",
    "Frequent on teenagers",
]

SOLR_URL = "http://localhost:8983/solr/disorders/select"
SOLR_URL2 = "http://localhost:8983/solr/disorders02/select"

settings_list = [
    {
        "defType": "edismax",
        "qf": "description^3 symptoms^2 causes^2 treatment^1.7 diagnosis^1.5 prevention^1.0 epidemiology^1.5 content^0.5",
        "pf": "description symptoms", # Phrase boost for field relevance
        "ps": 2, # Phrase slop allows slight separation in terms
        "ps2": 1, # Phrase slop for longer phrases
        "wt": "json", # JSON response format
        "rows": 25, # Number of results to return
        "fl": "name, link, description, symptoms, epidemiology"  # Fields to return
    },
]

def search_solr(question, mode, setting, number):
    try:
        if setting:
            settings = settings_list[setting-1]

        settings["q"] = question
        if mode == 1:
            response = requests.get(SOLR_URL, params=settings)
            print(f"\nRequest URL: {response.url}")
            response.raise_for_status()
            data = response.json()
            with open(f"solr/queries/schema_1/q{number}/answer.json", "w") as f:
                json.dump(data, f, indent=4)
        else:
            response = requests.get(SOLR_URL2, params=settings)
            print(f"\nRequest URL: {response.url}")
            response.raise_for_status()
            data = response.json()
            with open(f"solr/queries/schema_2/q{number}/answer.json", "w") as f:
                json.dump(data, f, indent=4)

        num_found = data['response']['numFound']

        print(f"\n{num_found} documents found.")

        # Print the details of each document

        for doc in data['response']['docs']:
            print("\nDocument:")
            for field, value in doc.items():
                if field == 'name':
                    print(f"  {field}: {value}")
                if field == 'link':
                    print(f"  {field}: {value}")
                if field == 'debug':
                    print(f"  {field}: {value}")
            print("----------------------------------")
        print("\n--- End of Results ---\n")

    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)



def main(mode, settings):
    print("Welcome to Solr Natural Language Search!")
    print("Type your question in natural language and press Enter. Type 'exit' to quit.\n")

    number = 0
    for query in queries:
        number += 1
        search_solr(query, mode, settings, number)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solr Natural Language Search")
    parser.add_argument("mode", type=int, default=1, help="Select Solr core (1 or 2)")
    parser.add_argument("setting", type=int, default=1, help="Select query settings (1, 2, ...)")
    args = parser.parse_args()
    main(args.mode, args.setting)
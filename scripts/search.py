import requests
import argparse
import json

SOLR_URL = "http://localhost:8983/solr/disorders/select"
SOLR_URL2 = "http://localhost:8983/solr/disorders02/select"

def search_solr(question, mode):
    # Configure query parameters to use edismax for natural language queries
    params = {
        "q": question,
        "defType": "edismax",
        "qf": "description^3 symptoms^2 causes^2 epidemiology^1.5 content^1",  # Boosts for key fields
        "pf": "description symptoms",       # Phrase boost for field relevance
        "ps": 2,                            # Phrase slop allows slight separation in terms
        "ps2": 1,                           # Phrase slop for longer phrases
        "wt": "json",                        # JSON response format
        "debugQuery": "true"
    }

    try:
        # Send the request to Solr
        if mode == 1:
            response = requests.get(SOLR_URL, params=params)
        else:
            response = requests.get(SOLR_URL2, params=params)
        print(f"\nRequest URL: {response.url}")
        response.raise_for_status()
        data = response.json()

        # Display results
        num_found = data['response']['numFound']
        print(f"\n{num_found} documents found.")
        
        # Print the details of each document
        for doc in data['response']['docs']:
            print("\nDocument:")
            for field, value in doc.items():
                #print(f"  {field}: {value}")
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

def main(mode):
    print("Welcome to Solr Natural Language Search!")
    print("Type your question in natural language and press Enter. Type 'exit' to quit.\n")

    while True:
        # Prompt the user for a natural language query
        question = input("Enter your question: ")
        
        if question.lower() == 'exit':
            print("Exiting Solr Interactive Search. Goodbye!")
            break

        # Perform the search and display results
        search_solr(question, mode)

if __name__ == "__main__":
    modes = {
        1: "Core disorders 01.",
        2: "Core disorders 02.",
    }
        
    parser = argparse.ArgumentParser(
        description="Interactive Solr Search.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        'mode',
        type=int,
        choices=modes.keys(),
        help='Options:\n' + '\n'.join([f"{k} - {v}" for k, v in modes.items()])
    )
    
    args = parser.parse_args()
    main(args.mode)

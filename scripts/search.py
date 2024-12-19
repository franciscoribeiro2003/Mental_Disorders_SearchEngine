import json
import os

import requests
import argparse

from sentence_transformers import SentenceTransformer

from scripts.rocchio import pseudo_rocchio_algorithm, rocchio_algorithm

SOLR_URL = "http://localhost:8983/solr/disorders/select"
SOLR_URL2 = "http://localhost:8983/solr/disorders02/select"
SOLR_URL3 = "http://localhost:8983/solr/disorders03/select"

queries = [
    "Cognitive speed",
    "Childhood trauma",
    "Improvement with behavioral therapies",
    "Frequent on childrens",
    "Caused by genetics inherited"
]


def get_relevant_non_relevant_vectors(n, data_resonse=None):
    """

    :param data_resonse: response for original string
    :param n: if its query for witch there is already defined relevance  (only for testing!)
    :return: lists of relevant and non-relevant vectors
    """
    if n != -1:
        top_k = 5
        base_path = os.path.dirname(__file__)
        relative_path = os.path.join(base_path, f"../solr/queries/schema_3/q{n}/evaluation.json")
        absolute_path = os.path.abspath(relative_path)
        with open(absolute_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        relevant_docs_ind = []
        non_relevant_docs_ind = []

        for doc_number, relevance in data.items():
            if relevance == 1:
                relevant_docs_ind.append(int(doc_number) - 1)
            else:
                non_relevant_docs_ind.append(int(doc_number) - 1)
        print(relevant_docs_ind)
        print(non_relevant_docs_ind)
        retrieved_docs_vectors = [doc['vector'] for doc in data_resonse['response']['docs']]
        relevant_docs = [retrieved_docs_vectors[ind] for ind in relevant_docs_ind]
        non_relevant_docs = [retrieved_docs_vectors[ind] for ind in non_relevant_docs_ind]
        return relevant_docs[:min(top_k, len(relevant_docs))], non_relevant_docs[:min(top_k, len(non_relevant_docs))]

    else:
        print("todo")


def text_to_embedding(text):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embedding = model.encode(text, convert_to_tensor=False).tolist()

    # Convert the embedding to the expected format
    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
    return embedding_str


def search_solr(question, mode, embedding=None):
    # Configure query parameters to use edismax for natural language queries
    params = {
        "q": question,
        "defType": "edismax",
        "qf": "description^3 symptoms^2 causes^2 epidemiology^1.5 content^1",  # Boosts for key fields
        "pf": "description symptoms",  # Phrase boost for field relevance
        "ps": 2,  # Phrase slop allows slight separation in terms
        "ps2": 1,  # Phrase slop for longer phrases
        "wt": "json",  # JSON response format
        "debugQuery": "true"
    }

    params_embbed = {
        "q": f"{{!knn f=vector topK=25}}{embedding}",
        "fl": "name,link",
        "rows": 25,
        "wt": "json"
    }

    if mode > 3:
        params_embbed["fl"] = "name,link,vector"
    if mode == 6:
        params_embbed = {
            "defType": "edismax",
            "q": f"{question}^0.3",
            "bq": f"{{!knn f=vector}}{embedding}",
            "qf": "description^3 symptoms^2 causes^2 treatment^1.7 diagnosis^1.5 prevention^1.0 epidemiology^1.5 "
                  "content^0.5",
            "pf": "description^4 symptoms^2 causes^2",
            "fl": "name,link,score,vector",
            "rows": "25",
            "wt": "json",
            "ps": "2",
            "ps2": "1"
        }

    try:
        # Send the request to Solr
        if mode == 1:
            response = requests.get(SOLR_URL, params=params)
        elif mode == 2:
            response = requests.get(SOLR_URL2, params=params)
        else:
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            response = requests.post(SOLR_URL3, data=params_embbed, headers=headers)

        if mode > 3:
            updated_query_vector = None
            query_vector = embedding
            data = response.json()
            if mode == 4 or mode == 6:
                # Pseudo Rocchio
                print(f"using pseudo-Rocchio for query:'{question}'")
                retrieved_docs_vectors = [doc['vector'] for doc in data['response']['docs']]
                # print(retrieved_docs_vectors)
                updated_query_vector = pseudo_rocchio_algorithm(query_vector, retrieved_docs_vectors)
            elif mode == 5:
                # Rocchio
                n = -1

                if question in queries:
                    n = queries.index(question) + 1

                print(f"using Rocchio for query:'{question} ({n})'")

                relevant_docs, non_relevant_docs = get_relevant_non_relevant_vectors(n, data)
                updated_query_vector = rocchio_algorithm(query_vector, relevant_docs, non_relevant_docs)

            if mode == 6:
                params_embbed["bq"] = f"{{!knn f=vector}}{updated_query_vector}"
            else:
                params_embbed["q"] = f"{{!knn f=vector topK=25}}{updated_query_vector}"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            response = requests.post(SOLR_URL3, data=params_embbed, headers=headers)

        print(f"\nRequest URL: {response.url}")
        response.raise_for_status()
        data = response.json()

        # Display results
        num_found = data['response']['numFound']
        print(f"\n{num_found} documents found.")

        ind = 1
        # Print the details of each document
        for doc in data['response']['docs']:
            print(f"\n{ind}. Document:")
            for field, value in doc.items():
                # print(f"  {field}: {value}")
                if field == 'name':
                    print(f"  {field}: {value}")
                if field == 'link':
                    print(f"  {field}: {value}")
                if field == 'debug':
                    print(f"  {field}: {value}")
            print("----------------------------------")
            ind += 1
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
        if mode >= 3:
            embedding = text_to_embedding(question)
            search_solr(question, mode, embedding)
        else:
            embedding = text_to_embedding(question)
            search_solr(question, mode, embedding)


if __name__ == "__main__":
    """
    modes = {
        1: "Core disorders 01.",
        2: "Core disorders 02.",
        3: "Core disorders 03.",
        4: "Core disorders 03 with pseudo rocchio.",
        5: "Core disorders 03 with  rocchio."
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

    main(args)
    """
    main(6)




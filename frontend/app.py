# app.py
from flask import Flask, render_template, request, jsonify
from sentence_transformers import SentenceTransformer
import numpy as np
import requests
import json

app = Flask(__name__)

solr_ip = "172.18.0.1"
SOLR_URLS = {
    1: f"http://{solr_ip}:8983/solr/disorders/select",
    2: f"http://{solr_ip}:8983/solr/disorders02/select",
    3: f"http://{solr_ip}:8983/solr/disorders03/select"
}

model = SentenceTransformer('all-MiniLM-L6-v2')


def text_to_embedding(text):
    embedding = model.encode(text, convert_to_tensor=False).tolist()
    return "[" + ",".join(map(str, embedding)) + "]"


def search_solr(query, mode=3, core=3):
    embedding = text_to_embedding(query)

    # Different parameters based on mode
    if mode <= 2:
        params = {
            "q": query,
            "defType": "edismax",
            "qf": "description^3 symptoms^2 causes^2 treatment^1.7 diagnosis^1.5 prevention^1.0 epidemiology^1.5 content^0.5",
            "pf": "description^4 symptoms^2 causes^2",  # Phrase boost for field relevance
            "ps": 2,  # Phrase slop allows slight separation in terms
            "ps2": 1,  # Phrase slop for longer phrases
            "wt": "json",  # JSON response format
            "rows": 25,  # Number of results to return
            "fl": "name, link, description, symptoms, epidemiology, score"  # Fields to return
        }
    elif mode == 6:  # Hybrid Search
        params = {
            "defType": "edismax",
            "q": f"{query}^0.3",
            "bq": f"{{!knn f=vector}}{embedding}",
            "qf": "description^3 symptoms^2 causes^2 treatment^1.7 diagnosis^1.5 prevention^1.0 epidemiology^1.5 content^0.5",
            "pf": "description^4 symptoms^2 causes^2",
            "fl": "name,link,score",
            "rows": "25",
            "wt": "json",
            "ps": "2",
            "ps2": "1"
        }

    else:
        params = {
            "q": f"{{!knn f=vector topK=25}}{embedding}",
            "fl": "name,link,vector,score" if mode > 3 else "name,link,score",
            "rows": 25,
            "wt": "json"
        }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        solr_url = SOLR_URLS[core]
        response = requests.post(solr_url, data=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Handle Rocchio algorithms for modes 4 and 5 if needed
        if mode == 4:
            # Pseudo Rocchio
            retrieved_docs_vectors = [doc['vector'] for doc in data['response']['docs']]
            updated_query_vector = pseudo_rocchio_algorithm(embedding, retrieved_docs_vectors)
            params["q"] = f"{{!knn f=vector topK=25}}{updated_query_vector}"
            response = requests.post(solr_url, data=params, headers=headers)
            data = response.json()
        elif mode == 5:
            # Regular Rocchio (simplified version without relevance feedback for now)
            retrieved_docs_vectors = [doc['vector'] for doc in data['response']['docs']]
            updated_query_vector = rocchio_algorithm(embedding, retrieved_docs_vectors, [])
            params["q"] = f"{{!knn f=vector topK=25}}{updated_query_vector}"
            response = requests.post(solr_url, data=params, headers=headers)
            data = response.json()

        return data
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def pseudo_rocchio_algorithm(query_vector, retrieved_docs_vectors, alpha=1.0, beta=0.75):
    # Simplified implementation
    query = eval(query_vector)
    retrieved = [eval(doc) for doc in retrieved_docs_vectors[:5]]  # Use top 5 documents

    query_array = np.array(query)
    retrieved_array = np.mean(np.array(retrieved), axis=0)

    updated_query = alpha * query_array + beta * retrieved_array
    return "[" + ",".join(map(str, updated_query.tolist())) + "]"


def rocchio_algorithm(query_vector, relevant_docs, non_relevant_docs, alpha=1.0, beta=0.75, gamma=0.15):
    # Simplified implementation
    query = eval(query_vector)
    relevant = [eval(doc) for doc in relevant_docs]
    non_relevant = [eval(doc) for doc in non_relevant_docs]

    query_array = np.array(query)
    relevant_array = np.mean(np.array(relevant), axis=0) if relevant else np.zeros_like(query_array)
    non_relevant_array = np.mean(np.array(non_relevant), axis=0) if non_relevant else np.zeros_like(query_array)

    updated_query = alpha * query_array + beta * relevant_array - gamma * non_relevant_array
    return "[" + ",".join(map(str, updated_query.tolist())) + "]"


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/search')
def search():
    query = request.args.get('q', '')
    mode = int(request.args.get('mode', 6))
    core = int(request.args.get('core', 3))

    if not query:
        return jsonify({"error": "No query provided"})

    results = search_solr(query, mode, core)
    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81, debug=True)
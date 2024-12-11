import json

import numpy as np


def rocchio_algorithm(query_vector, relevant_docs, non_relevant_docs=None, alpha=1, beta=1, gamma=0.5):
    """
    Implementation of user feedback Rocchio algorithm.Idea is to change query vector to move it closer to ideal vector
     for our information need by taking into account user feedback that defines classifies relevant and non-relevant
     documents of original query
    :param query_vector: original query vector
    :param relevant_docs: documents deemed as relevant by user
    :param non_relevant_docs: documents deemed as not relevant by user
    :param alpha: weight on original query
    :param beta: weight for relevant documents
    :param gamma: weight for not relevant documents
    :return: vector for new,improved query
    """
    query_vector = json.loads(query_vector)
    # Convert lists to numpy arrays for vector operations
    query_vector = np.array(query_vector, dtype=float)
    relevant_docs = np.array(relevant_docs, dtype=float)
    non_relevant_docs = np.array(non_relevant_docs, dtype=float)

    # Calculate the centroid of relevant documents
    if len(relevant_docs) > 0:
        relevant_centroid = np.mean(relevant_docs, axis=0)
    else:
        relevant_centroid = np.zeros_like(query_vector)

    # Calculate the centroid of non-relevant documents
    if len(non_relevant_docs) > 0:
        non_relevant_centroid = np.mean(non_relevant_docs, axis=0)
    else:
        non_relevant_centroid = np.zeros_like(query_vector)

    # Update the query vector using the Rocchio formula
    updated_query_vector = alpha * query_vector + beta * relevant_centroid - gamma * non_relevant_centroid
    updated_query_vector = np.maximum(updated_query_vector, 0)

    return updated_query_vector.tolist()


def pseudo_rocchio_algorithm(query_vector, retrieved_docs, top_k=4, alpha=1, beta=0.75):
    """
    Implementation of psudo-feedback Rocchio algorithm.Idea is that top k results are most probbably relevant so
    we change query vector to better fit those documents and to move it closer to ideal vector for our information need
    :param query_vector: original query vector
    :param retrieved_docs: documents retrived by original query (vectors)
    :param top_k: amount of best ranked documents that will be deemed relevant
    :param alpha: weight for original query
    :param beta: weight for relevant documents
    :return:
    """

    query_vector = json.loads(query_vector)
    # Convert lists to numpy arrays for vector operations
    query_vector = np.array(query_vector, dtype=float)
    retrieved_docs = np.array(retrieved_docs, dtype=float)

    # Split the retrieved documents into relevant and non-relevant
    relevant_docs = retrieved_docs[:top_k]

    # Calculate the centroid of relevant documents
    if len(relevant_docs) > 0:
        relevant_centroid = np.mean(relevant_docs, axis=0)
    else:
        relevant_centroid = np.zeros_like(query_vector)

    # Update the query vector using the Rocchio formula
    updated_query_vector = alpha * query_vector + beta * relevant_centroid

    return updated_query_vector.tolist()

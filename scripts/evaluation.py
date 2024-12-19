import json
import matplotlib.pyplot as plt
import argparse

LIMIT = 25
PRECISION_AT = 25
QUERIES = 5
SCHEMAS = 2

schemas_dict = {
    1 : "simple",
    2 : "better lexical",
    3 : "simple semantic",

}

"""
read the evaluation file for @query in @schema
"""
def getResults(query: int, schema: str) -> list:
    path = f"../solr/queries/schema_{schema}/q{query}/evaluation.json"
    with open(path, 'r') as file:
        data = json.load(file)
        file.close()

    results = data.values()
    return list(results)


def recall_at_k(results: list, k: int) -> float:
    return len([
        result for result in results[:k] if result == 1
    ]) / len(results)


def precision_values(results: list) -> float:
    return [
        len([
            doc for doc in results[:idx] if doc == 1
        ]) / idx
        for idx, _ in enumerate(results, start=1)
    ]


def recall_values(results: list) -> float:
    return [
        (len([
            doc for doc in results[:idx] if doc == 1
        ]) / sum(results)) if sum(results) else 0
        for idx, _ in enumerate(results, start=1)
    ]


# MAP
def mean_average_precision(stats, schemas):

    result = {schema: 0 for schema in schemas}
    count = {schema: 0 for schema in schemas}

    for entry in stats:
        schema = entry["schema"]
        average_precision = entry["AvP"]


        result[int(schema)] += average_precision
        count[int(schema)] += 1

    for schema in schemas:
        result[schema] /= count[schema] if count[schema] > 0 else 1

    return result


# P@K - Precision At K
def precision_at_k(results: list, k: int = PRECISION_AT) -> float:
    return len([
        result for result in results[:k] if result == 1
    ]) / k


# AvP - Average Precision
def average_precision(results: list) -> float:
    precisions = precision_values(results)
    return round(sum(precisions) / len(results), 2)


# Recall
def recall(results: list) -> float:
    return round(sum(recall_values(results)), 2)


# Accumulative curves
def acc_results(precision, recall):
    maximos = []

    for _, r in zip(precision, recall):
        max_precision = max([p_i for (p_i, r_i) in zip(precision, recall) if r_i >= r])
        maximos.append(max_precision)

    return maximos


# Precision-Recall Curves
def precision_recall(results: list, tuple, query: int) -> None:
    precision_results = [round(v, 2) for v in precision_values(results)]
    recall_results = [round(v, 2) for v in recall_values(results)]

    x = [round(0.04 * x, 2) for x in range(1, 26)]
    y = acc_results(precision_results, recall_results)

    plt.xlim(0, 1.1)
    plt.ylim(0, 1.1)

    if tuple[0] == 1:
        schema = "simple"
    else:
        schema = "better"

    plt.plot(x, y, label='Precision-Recall Curve')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title(f'Precision-Recall Curve Q{query} ({schema} schema)')
    plt.legend()
    plt.savefig(f"../solr/queries/schema_{tuple[0]}/q{tuple[1]}/PR_curve_s{tuple[0]}q{tuple[1]}.png")
    plt.close()

def precision_recall_compare(results: dict, query: int, schemas: list[int]) -> None:
    plt.figure()
    for schema in schemas:
        precision_results = [round(v, 2) for v in precision_values(results[schema, query])]
        recall_results = [round(v, 2) for v in recall_values(results[schema, query])]

        x = [round(0.04 * x, 2) for x in range(1, 26)]
        y = acc_results(precision_results, recall_results)


        schema_name = schemas_dict[schema]
        allschemas = "".join(map(str, schemas))

        plt.plot(x, y, label=f'Precision-Recall Curve ({schema_name} schema)')

    plt.xlim(0, 1.1)
    plt.ylim(0, 1.1)
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title(f'Precision-Recall Curve Comparison Q{query}')
    plt.legend()
    plt.savefig(f"../solr/evaluation/combined_PR_curve_q{query}_s{allschemas}.png")
    plt.close()

def compute_rcs(results: dict, query: int):
    for k, v in results.items():
        precision_recall(v, k, query)


def print_stats(stats: dict) -> None:
    for key, value in stats.items():
        print(f"{key}: {value}")


def evaluate(query: int, schema: str) -> list:
    results = getResults(query, schema)
    stats = {
        'query': f'q{query}',
        'schema': schema,
        f'P@{PRECISION_AT}': precision_at_k(results),
        'AvP': average_precision(results),
    }

    return [stats, results]




def combine_all_queries_graph(results: dict, schemas: list[int]) -> None:
    plt.figure()

    for schema in schemas:
        all_precision_results = []
        all_recall_results = []

        for query in range(1, QUERIES + 1):
            precision_results = [round(v, 2) for v in precision_values(results[schema, query])]
            recall_results = [round(v, 2) for v in recall_values(results[schema, query])]
            all_precision_results.append(precision_results)
            all_recall_results.append(recall_results)

        # Calculate average precision and recall values
        avg_precision_results = [sum(x) / len(x) for x in zip(*all_precision_results)]
        avg_recall_results = [sum(x) / len(x) for x in zip(*all_recall_results)]

        x = [round(0.04 * x, 2) for x in range(1, 26)]
        y = acc_results(avg_precision_results, avg_recall_results)

        schema_name = schemas_dict[schema]
        plt.plot(x, y, label=f'Average Precision-Recall Curve ({schema_name} schema)')

    plt.xlim(0, 1.1)
    plt.ylim(0, 1.1)
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Average Precision-Recall Curve Comparison for All Queries')
    plt.legend()
    plt.savefig(f"../solr/evaluation/combined_PR_curve_all_queries.png")
    plt.close()

def main(milestone, mode):

    schemas = [1,2]
    if milestone not in [2, 3]:
        print("Invalid milestone. Please provide 2 or 3.")
        return

    if milestone == 3:
        schemas = [2,3]


    stats = []
    results = {}
    for query in range(1, QUERIES + 1):
        for schema in schemas:
            output = evaluate(query, str(schema))
            stats.append(output[0])
            results[schema, query] = output[1]

        if mode == 'separate':
            compute_rcs(results, query)
        elif mode == "combined":
            precision_recall_compare(results, query, schemas)
        elif mode == ".":
            compute_rcs(results, query)
            precision_recall_compare(results, query, schemas)

        else:
            print("Invalid mode. Please provide 'separate', 'combined' or '.'.")
            return

    combine_all_queries_graph(results, schemas)
    output = {
        'Results per query and per mode': stats,
        'Global MAP': mean_average_precision(stats, schemas),
    }

    print(json.dumps(output, indent=2))

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Solr Evaluation")
    parser.add_argument("milestone", type=int, help="Select the milestone to evaluate")
    parser.add_argument("mode", type=str, help="Select the type of evaluation")
    args = parser.parse_args()
    
    main(args.milestone, args.mode)

    #main(3,".")

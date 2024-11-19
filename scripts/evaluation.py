import json
import matplotlib.pyplot as plt
import argparse

LIMIT = 25
PRECISION_AT = 25
QUERIES = 5
SCHEMAS = 2

"""
read the evaluation file for @query in @schema
"""
def getResults(query: int, schema: str) -> list:
    path = f"solr/queries/schema_{schema}/q{query}/evaluation.json"
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
def mean_average_precision(stats):

    result = {schema: 0 for schema in range(1,SCHEMAS+1)}
    count = {schema: 0 for schema in range(1,SCHEMAS+1)}

    for entry in stats:
        schema = entry["schema"]
        average_precision = entry["AvP"]


        result[int(schema)] += average_precision
        count[int(schema)] += 1

    for schema in range(1, SCHEMAS+1):
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
    plt.savefig(f"solr/queries/schema_{tuple[0]}/q{tuple[1]}/PR_curve_s{tuple[0]}q{tuple[1]}.png")
    plt.close()

def precision_recall_compare(results: dict, query: int, schemas: int) -> None:
    plt.figure()
    for schema in range(1, schemas + 1):
        precision_results = [round(v, 2) for v in precision_values(results[schema, query])]
        recall_results = [round(v, 2) for v in recall_values(results[schema, query])]

        x = [round(0.04 * x, 2) for x in range(1, 26)]
        y = acc_results(precision_results, recall_results)

        if schema == 1:
            schema_name = "simple"
        else:
            schema_name = "better"

        plt.plot(x, y, label=f'Precision-Recall Curve ({schema_name} schema)')

    plt.xlim(0, 1.1)
    plt.ylim(0, 1.1)
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title(f'Precision-Recall Curve Comparison Q{query}')
    plt.legend()
    plt.savefig(f"solr/evaluation/combined_PR_curve_q{query}.png")
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


def main(milestone, mode):
    if milestone not in [2, 3]:
        print("Invalid milestone. Please provide 2 or 3.")
        return

    if milestone == 3:
        print("Milestone 3 implementation is not finished.")
        return

    stats = []
    results = {}
    for query in range(1, QUERIES + 1):
        for schema in range(1, SCHEMAS + 1):
            output = evaluate(query, str(schema))
            stats.append(output[0])
            results[schema, query] = output[1]

        if mode == "separate":
            compute_rcs(results, query)
        elif mode == "combined":
            precision_recall_compare(results, query, SCHEMAS)
        elif mode == "*":
            compute_rcs(results, query)
            precision_recall_compare(results, query, SCHEMAS)
        else:
            print("Invalid mode. Please provide 'separate', 'combined' or '*'.")
            return

    output = {
        'Results per query and per mode': stats,
        'Global MAP': mean_average_precision(stats),
    }

    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solr Evaluation")
    parser.add_argument("milestone", type=int, help="Select the milestone to evaluate")
    parser.add_argument("mode", type=str, help="Select the type of evaluation")
    args = parser.parse_args()
    main(args.milestone, args.mode)

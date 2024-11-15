import argparse
import sys
import json

def print_disorders_names(input_json_file):
    with open(input_json_file, 'r') as file:
        data = json.load(file)
        for disorder in data:
            print(disorder['name'])



def main(mode, input_json_file):
    if mode == 1:
        print_disorders_names(input_json_file)
    else:
        print("Invalid mode selected. Use --help for more information.")

if __name__ == "__main__":
    modes = {
        1: "Print all the disorders names inside the select json file.",
    }

    parser = argparse.ArgumentParser(
        description="Mental disorders gathering data.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'mode',
        type=int,
        choices=modes.keys(),
        help='Options:\n' + '\n'.join([f"{k} - {v}" for k, v in modes.items()])
    )
    parser.add_argument(
        'input_json_file',
        type=str,
        help='Path to the input JSON file.'
    )

    args = parser.parse_args()

    if args.mode is None:
        parser.print_help()
        sys.exit(1)

    # Pass the mode, input, and output files to the main function
    main(args.mode, args.input_json_file)
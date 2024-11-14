import json

# Load the JSON data from the file
with open('C:/Users/Toni/Projects/Porto/IP&R/Mental_Disorders_SearchEngine/data/disorders_cleaned_final.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Extract the name of every disorder
disorder_names = [disorder['name'] for disorder in data]

# Print the names of the disorders
with open('disorder_names.txt', 'w', encoding='utf-8') as file:
    for name in disorder_names:
        file.write(name + '\n')
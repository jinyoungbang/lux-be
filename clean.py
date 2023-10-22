import json
import os

# Load the JSON file
with open('output.json', 'r') as file:
    data = json.load(file)

data = data["data"]
new_data = []

for transaction in data:
    if transaction["name"] == "Tectra Inc":
        continue

    new_data.append(transaction)

final_data = {
    "data": new_data
}
# Save the modified JSON to a new file
with open('output.json', 'w') as file:
    json.dump(final_data, file, indent=4)

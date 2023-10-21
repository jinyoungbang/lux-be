import json

with open("data.json", "r") as file:
    data = json.load(file)

data = data["data"]
print(len(data))
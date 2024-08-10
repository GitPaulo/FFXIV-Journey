import pandas as pd
import json
import requests
import time
from tqdm import tqdm
from io import StringIO

# Raw CSV URL for the Quest data
csv_url = 'https://raw.githubusercontent.com/xivapi/ffxiv-datamining/master/csv/Quest.csv'
response = requests.get(csv_url)
if response.status_code == 200:
    csv_content = response.content.decode('utf-8')
    print("Quest.csv downloaded successfully.")
else:
    print(f"Failed to download Quest.csv. Status code: {response.status_code}")
    exit()

# Load the CSV content into a DataFrame, skip the first and third rows, and use the second row as the header
usecols = ["#", "Name", "Id", "Expansion", "EventIconType", "PreviousQuest[0]", "PreviousQuest[1]", "PreviousQuest[2]", "PreviousQuest[3]"]
quest_data = pd.read_csv(StringIO(csv_content), skiprows=[0, 2], low_memory=False, usecols=usecols)

# Drop rows where 'Name' column has NaN values
quest_data = quest_data.dropna(subset=['Name'])

# Filter to keep rows where EventIconType is 3 which represents Main Scenario Quests
filtered_data = quest_data[quest_data['EventIconType'] == 3]

# Detect starting location based on the quest ID prefix
def detect_starting_location(quest_id):
    if "Fst" in quest_id:
        return "Gridania"
    elif "Sea" in quest_id:
        return "Limsa Lominsa"
    elif "Wil" in quest_id:  
        return "Ul'dah"
    else:
        return None

# Convert expansion number to expansion name
def convert_expansion_number_to_name(expansion_number):
    if expansion_number == 0:
        return "A Realm Reborn"
    elif expansion_number == 1:
        return "Heavensward"
    elif expansion_number == 2:
        return "Stormblood"
    elif expansion_number == 3:
        return "Shadowbringers"
    elif expansion_number == 4:
        return "Endwalker"
    elif expansion_number == 5:
        return "Dawntrail"
    else:
        return "Unknown"

# Fetch the Image path for each quest (this part can be skipped if necessary)
api_base_url = "https://beta.xivapi.com/api/1/search"
quests_by_number = {}

# Prompt user if they want to fetch images
fetch_images = input("Do you want to fetch images? (yes/no): ").strip().lower() == 'yes'

with tqdm(total=len(filtered_data), desc="Processing Quests", ncols=100) as pbar:
    for _, row in filtered_data.iterrows():
        quest_name = row["Name"]
        starting_location = detect_starting_location(row["Id"])
        expansion_name = convert_expansion_number_to_name(row["Expansion"])

        # Optionally fetch the Image path
        image_path = None
        if fetch_images:
            response = requests.get(
                api_base_url, 
                params={
                    "sheets": "Quest",
                    "query": f"Name~\"{quest_name}\"",
                    "fields": "Icon,Name"
                }
            )
            if response.status_code == 200:
                data = response.json()
                if data["results"]:
                    image_path = data["results"][0]["fields"]["Icon"]["path_hr1"]

            # To avoid hitting the API rate limit
            time.sleep(0.100)
        
        # Create the quest entry
        quest = {
            "#": row["#"],
            "Id": row["Id"],
            "Name": row["Name"],
            "Expansion": expansion_name,
            "EventIconType": row["EventIconType"],
            "PreviousQuests": [row[col] for col in ["PreviousQuest[0]", "PreviousQuest[1]", "PreviousQuest[2]", "PreviousQuest[3]"] if not pd.isna(row[col])],
            "NextMSQ": None,  # Initialize as None, to be filled later
            "StartingLocation": starting_location,
            "Image": image_path
        }
        quests_by_number[row["#"]] = quest

        pbar.update(1)

# Calculate the next MSQ for each quest
for quest in quests_by_number.values():
    for previous_quest_number in quest["PreviousQuests"]:
        if previous_quest_number in quests_by_number:
            quests_by_number[previous_quest_number]["NextMSQ"] = quest["#"]

# Remove quests that do not have a NextMSQ but are not final quests,
# but keep the quest with the highest # number.
max_quest_id = max(quests_by_number.keys())
quests_by_number = {
    quest_id: quest for quest_id, quest in quests_by_number.items()
    if quest["NextMSQ"] or quest_id == max_quest_id
}

print(f"After filtering, {len(quests_by_number)} quests remain.")

# Filter out duplicate quests with the same Name, NextMSQ, and StartingLocation
seen_quests = {}
filtered_quests_by_number = {}
for quest_id, quest in quests_by_number.items():
    key = (quest["Name"], quest["NextMSQ"], quest["StartingLocation"])
    if key not in seen_quests:
        seen_quests[key] = quest_id
        filtered_quests_by_number[quest_id] = quest

# Update quests_by_number to only include filtered quests
quests_by_number = filtered_quests_by_number

print(f"After removing duplicates, {len(quests_by_number)} quests remain.")


# Organize the data into the desired structure with correct MSQ order
quests_by_expansion = {}

for quest in quests_by_number.values():
    expansion = quest["Expansion"]
    starting_location = quest["StartingLocation"] if quest["StartingLocation"] else "Main Quest Line"
    
    if expansion not in quests_by_expansion:
        quests_by_expansion[expansion] = {}
    
    if starting_location not in quests_by_expansion[expansion]:
        quests_by_expansion[expansion][starting_location] = []
    
    quests_by_expansion[expansion][starting_location].append(quest)

# Convert the dictionary into the desired array format
quests_array = []
for expansion, locations in quests_by_expansion.items():
    quests_array.append({
        "name": expansion,
        "quests": locations
    })

# Save the structured data to a JSON file
output_json_path = 'static/Quests.json'  # svelte app expects the file to be in the static folder
with open(output_json_path, 'w') as json_file:
    json.dump(quests_array, json_file, indent=4)

print(f'Filtered data saved to {output_json_path}')

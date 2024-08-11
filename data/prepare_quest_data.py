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

# Load the CSV content and include the first 1523 columns (including the penultimate column)
quest_data = pd.read_csv(StringIO(csv_content), skiprows=[0, 2], low_memory=False)

# Drop rows where 'Name' column has NaN values
quest_data = quest_data.dropna(subset=['Name'])

# Filter to keep rows where EventIconType is 3 which represents Main Scenario Quests
filtered_data = quest_data[quest_data['EventIconType'] == 3]

# Access the penultimate column by its index (-2) and filter out obsolete quests
filtered_data = filtered_data[filtered_data.iloc[:, -2] == False]

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
        starting_location = None
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

# Define the quests to start from and their corresponding locations
envoy_quests = {
    "The Ul'dahn Envoy": "Ul'dah",
    "The Lominsan Envoy": "Limsa Lominsa",
    "The Gridanian Envoy": "Gridania"
}
envoy_quests_data = filtered_data[filtered_data['Name'].isin(envoy_quests.keys())]

# Traverse backwards from each envoy quest and assign starting locations
if not envoy_quests_data.empty:
    for _, envoy_quest in envoy_quests_data.iterrows():
        location = envoy_quests[envoy_quest['Name']]
        print(f"\nAssigning starting location '{location}' by traversing backwards from '{envoy_quest['Name']}' with ID: {envoy_quest['#']}")
        
        current_quest = envoy_quest
        while current_quest is not None:
            print(f"Assigning '{location}' to quest: {current_quest['Name']}, ID: {current_quest['#']}")
            quests_by_number[current_quest['#']]['StartingLocation'] = location
            
            # Find the previous quest(s)
            previous_quest_ids = [str(current_quest[f'PreviousQuest[{i}]']).strip() for i in range(4) if not pd.isna(current_quest[f'PreviousQuest[{i}]'])]

            # Move to the first available previous quest that is also an MSQ (EventIconType == 3)
            current_quest = None
            for prev_id in previous_quest_ids:
                potential_quest = filtered_data.loc[(filtered_data['#'].astype(str).str.strip() == prev_id) & (filtered_data['EventIconType'] == 3)]
                
                if not potential_quest.empty:
                    current_quest = potential_quest.iloc[0]
                    break
else:
    print("No envoy quests were found in the data.")

# Calculate the next MSQ for each quest
for quest in quests_by_number.values():
    for previous_quest_number in quest["PreviousQuests"]:
        if previous_quest_number in quests_by_number:
            quests_by_number[previous_quest_number]["NextMSQ"] = quest["#"]

print(f"NextMSQ calculated to {len(quests_by_number)} quests.")

# Remove quests that do not have a NextMSQ but are not final quests,
# but keep the quest with the highest # number.
max_quest_id = max(quests_by_number.keys())
quests_by_number = {
    quest_id: quest for quest_id, quest in quests_by_number.items()
    if quest["NextMSQ"] or quest_id == max_quest_id
}

print(f"After filtering no NextMSQ, {len(quests_by_number)} quests remain.")

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

# Extract A Realm Reborn quests
arr_quests = [quest for quest in quests_by_number.values() if quest["Expansion"] == "A Realm Reborn"]

# Function to order quests based on the NextMSQ path, considering StartingLocation
def order_quests_by_next_msq(quests, location=None):
    # Create a mapping from quest ID to quest
    quest_map = {quest["#"]: quest for quest in quests}
    
    # Find the starting quests (which do not appear in any NextMSQ)
    start_quests = {quest["#"] for quest in quests} - {quest["NextMSQ"] for quest in quests if quest["NextMSQ"]}

    if not start_quests:
        print(f"No starting quest found in the A Realm Reborn category for {location if location else 'Main Quest Line'}. Skipping...")
        return []

    # Track processed quests to avoid duplicates
    processed_quests = set()
    
    # There might be multiple starting quests, so we handle each path separately
    sorted_quests = []
    for start_quest_id in start_quests:
        current_quest_id = start_quest_id
        while current_quest_id:
            if current_quest_id not in quest_map:
                print(f"Warning: Quest ID {current_quest_id} not found in quest_map. Skipping.")
                break

            if current_quest_id in processed_quests:
                print(f"Skipping duplicate quest ID {current_quest_id}.")
                break
            
            current_quest = quest_map[current_quest_id]
            sorted_quests.append(current_quest)
            processed_quests.add(current_quest_id)  # Mark this quest as processed
            
            next_msq_id = current_quest["NextMSQ"]

            if next_msq_id and next_msq_id in quest_map:
                current_quest_id = next_msq_id
            else:
                current_quest_id = None  # End of chain

    return sorted_quests

# Sort the A Realm Reborn quests by location
sorted_quests_by_location = {}
locations = ["Gridania", "Ul'dah", "Limsa Lominsa"]

# Process each starting location
for location in locations:
    location_quests = [quest for quest in quests_by_expansion["A Realm Reborn"].get(location, [])]
    if location_quests:  # Only process if there are quests for this location
        sorted_quests_by_location[location] = order_quests_by_next_msq(location_quests, location)

len_gridania = len(sorted_quests_by_location.get("Gridania", []))
len_uldah = len(sorted_quests_by_location.get("Ul'dah", []))
len_limsa_lominsa = len(sorted_quests_by_location.get("Limsa Lominsa", []))
print(f"Sorted ARR location quests length: Gridania: {len_gridania}, Ul'dah: {len_uldah}, Limsa Lominsa: {len_limsa_lominsa}")

# Handle the Main Quest Line
main_quest_line_quests = [quest for quest in quests_by_expansion["A Realm Reborn"].get("Main Quest Line", [])]
if main_quest_line_quests:
    sorted_quests_by_location["Main Quest Line"] = order_quests_by_next_msq(main_quest_line_quests, "Main Quest Line")

print(f"Sorted ARR Main Quest Line quests length: {len(sorted_quests_by_location['Main Quest Line'])}")

# Combine all sorted quests back into the quests_by_expansion structure
quests_by_expansion["A Realm Reborn"] = sorted_quests_by_location

# Validation function to check the integrity of the NextMSQ chain
def validate_next_msq_chain(sorted_quests):
    for quest_list in sorted_quests.values():
        for i in range(len(quest_list) - 1):
            current_quest = quest_list[i]
            next_quest = quest_list[i + 1]
            if current_quest["NextMSQ"] != next_quest["#"]:
                print(f"Validation error: Quest '{current_quest['Name']}' (ID: {current_quest['#']}) does not correctly link to '{next_quest['Name']}' (ID: {next_quest['#']}).")

# Validate the NextMSQ chain for each location and Main Quest Line
validate_next_msq_chain(sorted_quests_by_location)

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

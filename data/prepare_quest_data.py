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
usecols = ["#", "Name", "Id", "Expansion", "EventIconType", "PreviousQuest[0]"]
quest_data = pd.read_csv(StringIO(csv_content), skiprows=[0, 2], low_memory=False, usecols=usecols)

# Drop rows where 'Name' column has NaN values
quest_data = quest_data.dropna(subset=['Name'])

# Filter to keep rows where EventIconType is 3 which represents Main Scenario Quests
filtered_data = quest_data[quest_data['EventIconType'] == 3]

# Fetch the Image path for each quest
api_base_url = "https://beta.xivapi.com/api/1/search"
quests_by_number = {}
with tqdm(total=len(filtered_data), desc="Fetching Images", ncols=100) as pbar:
    # Populate the dictionary with quest data
    for _, row in filtered_data.iterrows():
        quest_name = row["Name"]
        
        # Make API call to fetch the Image path
        response = requests.get(
            api_base_url, 
            params={
                "sheets": "Quest",
                "query": f"Name~\"{quest_name}\"",
                "fields": "Icon,Name"
            }
        )
        
        image_path = None
        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                image_path = data["results"][0]["fields"]["Icon"]["path_hr1"]

        quest = {
            "#": row["#"],
            "Id": row["Id"],
            "Name": row["Name"],
            "Expansion": row["Expansion"],
            "EventIconType": row["EventIconType"],
            "PreviousQuest": row["PreviousQuest[0]"],
            "NextQuest": None,  # Initialize as None, to be filled later
            "Image": image_path
        }
        quests_by_number[row["#"]] = quest

        # Wait for 100ms to avoid hitting the API rate limit
        # Rate limit is 20 requests per second (1000ms/20 = 50ms) so we double it
        time.sleep(.100)

        # Update the progress bar
        pbar.update(1)

# Calculate the next quest for each quest
for quest in quests_by_number.values():
    previous_quest_number = quest["PreviousQuest"]
    if previous_quest_number in quests_by_number:
        quests_by_number[previous_quest_number]["NextQuest"] = quest["#"]

# Save the filtered data to a JSON file for use in the application
quests_list = list(quests_by_number.values())
output_json_path = 'data/Quests.json'
with open(output_json_path, 'w') as json_file:
    json.dump(quests_list, json_file, indent=4)

print(f'Filtered data saved to {output_json_path}')

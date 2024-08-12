import pandas as pd
import json
import requests
import time

from tqdm import tqdm
from io import StringIO

# Constants
RAW_QUESTS_CSV = 'https://raw.githubusercontent.com/xivapi/ffxiv-datamining/master/csv/Quest.csv'
RAW_EXVERSION_CSV = 'https://raw.githubusercontent.com/xivapi/ffxiv-datamining/master/csv/ExVersion.csv'
RAW_JOURNAL_BASE_CSV_URL = 'https://raw.githubusercontent.com/xivapi/ffxiv-datamining/master/csv/quest' # + expansion_number_to_three_digits + quest_id + '.csv'
XIV_API_SEARCH_BASE_URL = "https://beta.xivapi.com/api/1/search"
OUTPUT_JSON_PATH = 'static/Quests.json'

# Quest Group Constants
# Necessary hardcoded data to figure out ARR forking quest lines
QUEST_GROUP_GRIDANIA = "Gridania"
QUEST_GROUP_ULDAH = "Ul'dah"
QUEST_GROUP_LIMSA_LOMINSA = "Limsa Lominsa"
QUEST_GROUP_MAIN_QUEST_LINE = "Main Quest Line"
QUEST_GROUPS = [QUEST_GROUP_GRIDANIA, QUEST_GROUP_ULDAH, QUEST_GROUP_LIMSA_LOMINSA, QUEST_GROUP_MAIN_QUEST_LINE]

ENVOY_TO_QUEST_GROUP = {
    "The Ul'dahn Envoy": QUEST_GROUP_ULDAH,
    "The Lominsan Envoy": QUEST_GROUP_LIMSA_LOMINSA,
    "The Gridanian Envoy": QUEST_GROUP_GRIDANIA
}

STARTING_QUEST_IDS = [65621, 66104, 65644] # IDs for the "Close to Home" quests in Gridania, Ul'dah, and Limsa Lominsa

# Variable to keep track of the last successful expansion number
last_successful_folder_index = 0
def fetch_first_journal_entry(quest_id, max_folder_number=100, max_retries=5, delay=2, start_from_last_success=True):
    global last_successful_folder_index
    start_index = last_successful_folder_index if start_from_last_success else 0
    for folder_index in range(start_index, max_folder_number + 1):
        csv_url = f"{RAW_JOURNAL_BASE_CSV_URL}/{str(folder_index).zfill(3)}/{quest_id}.csv"
        # print(f"Trying URL: {csv_url}")
        # Attempt to fetch the CSV file with retries
        for attempt in range(max_retries):
            try:
                response = requests.get(csv_url)
                if response.status_code == 200:
                    csv_content = response.content.decode('utf-8')
                    # Load the CSV data into a DataFrame
                    # Skip the first 3 rows (header and metadata)
                    journal_data = pd.read_csv(StringIO(csv_content), skiprows=3)
                    if not journal_data.empty and journal_data.shape[1] >= 3:
                        last_successful_folder_index = folder_index
                        return journal_data.iloc[0, 2] # Accessing the third column (index 2)
                    else:
                        break  # Break the retry loop if data format is incorrect
                elif response.status_code == 404:
                    # If a 404 error is received, continue to the next expansion number
                    break
            except requests.exceptions.RequestException as e:
                print(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                # Wait before retrying
                time.sleep(delay)
    return None

def fetch_image_path(quest_name):
    image_path = None
    response = requests.get(
        XIV_API_SEARCH_BASE_URL, 
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
    
    return image_path

def load_expansion_mapping():
    response = requests.get(RAW_EXVERSION_CSV)
    if response.status_code == 200:
        csv_content = response.content.decode('utf-8')
        exversion_data = pd.read_csv(StringIO(csv_content), skiprows=[0, 2])
        # Create a mapping of index to expansion name
        return {row['#']: row['Name'] for _, row in exversion_data.iterrows()}
    else:
        print(f"Failed to download ExVersion.csv. Status code: {response.status_code}")
        exit()

def envoy_quests_from_data(data):
    return data[data['Name'].isin(ENVOY_TO_QUEST_GROUP.keys())]

def get_expansion_name(expansion_index, expansion_mapping):
    return expansion_mapping.get(expansion_index, "Unknown")

def get_previous_quests(row):
    return [int(row[f'PreviousQuest[{i}]']) for i in range(4) if not pd.isna(row[f'PreviousQuest[{i}]']) and str(row[f'PreviousQuest[{i}]']).strip() != '0']

# Index -> Expansion Name mapping
expansion_mapping = load_expansion_mapping()

# Raw CSV URL for the Quest data
response = requests.get(RAW_QUESTS_CSV)
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

# Prompt user if they want to fetch images
fetch_images = input("Do you want to fetch images? (yes/no): ").strip().lower() == 'yes'

# Prompt user if they want to fetch journal entries
fetch_journal_entries = input("Do you want to fetch journal entries? (yes/no): ").strip().lower() == 'yes'

# # -> Quest (formatted) mapping
quests_by_number = {}
with tqdm(total=len(filtered_data), desc="Processing Quests", ncols=100) as pbar:
    for _, row in filtered_data.iterrows():
        quest_name = row["Name"]
        quest_id = row["Id"]
        quest_number = row["#"]
        quest_icon_type = row["EventIconType"]
        quest_group = None
        expansion_name = get_expansion_name(row["Expansion"], expansion_mapping)

        # Optionally fetch the Image path
        image_path = None
        if fetch_images:
            image_path = fetch_image_path(quest_name) or None
            # To avoid hitting the API rate limit
            time.sleep(0.050)
        
        journal_entry = None
        if fetch_journal_entries:
            journal_entry = fetch_first_journal_entry(quest_id) or None
            time.sleep(0.050)
        
        # Create the quest entry
        quest = {
            "#": quest_number,
            "Id": quest_id,
            "Name": quest_name,
            "Description": journal_entry,
            "ExpansionName": expansion_name,
            "EventIconType": quest_icon_type,
            "PreviousQuests": get_previous_quests(row),
            "NextMSQ": None,  # Initialize as None, to be filled later
            "QuestGroup": quest_group,
            "Image": image_path
        }
        quests_by_number[quest_number] = quest

        pbar.update(1)

# Calculate ARR quest groups based on quests that lead to the envoy quests
envoy_quests = envoy_quests_from_data(filtered_data)
if envoy_quests.empty:
    raise ValueError("No envoy quests found in the filtered data.")
for _, envoy_quest in envoy_quests.iterrows():
    group = ENVOY_TO_QUEST_GROUP[envoy_quest['Name']]
    print(f"\nAssigning quest group '{group}' by traversing backwards from '{envoy_quest['Name']}' with ID: {envoy_quest['#']}")
    current_quest = envoy_quest
    while current_quest is not None:
        print(f"Assigning '{group}' to quest: {current_quest['Name']}, ID: {current_quest['#']}")
        quests_by_number[current_quest['#']]['QuestGroup'] = group
        # Find the previous quest(s)
        previous_quest_ids = get_previous_quests(current_quest)
        # Move to the first available previous quest that is also an MSQ (EventIconType == 3)
        current_quest = None
        for prev_id in previous_quest_ids:
            potential_quest = filtered_data.loc[(filtered_data['#'] == prev_id) & (filtered_data['EventIconType'] == 3)]
            if not potential_quest.empty:
                current_quest = potential_quest.iloc[0]
                break

# Build a linked list of quests based on the NextMSQ field
for quest in quests_by_number.values():
    for previous_quest_number in quest["PreviousQuests"]:
        if quests_by_number.get(previous_quest_number):
            quests_by_number[previous_quest_number]["NextMSQ"] = quest["#"]
            # print(f"Quest {previous_quest_number} -> NextMSQ: {quest['#']}")

# Remove quests that do not have a NextMSQ but are not final quests,
# but keep the quest with the highest # number.
max_quest_id = max(quests_by_number.keys())
quests_by_number = {
    quest_id: quest for quest_id, quest in quests_by_number.items()
    if quest["NextMSQ"] or quest_id == max_quest_id
}

print(f"After filtering no NextMSQ, {len(quests_by_number)} quests remain.")

# Organize the data into the desired structure with correct MSQ order
quests_by_expansion = {}
for quest in quests_by_number.values():
    expansion = quest["ExpansionName"]
    quest_group = quest["QuestGroup"] if quest["QuestGroup"] else QUEST_GROUP_MAIN_QUEST_LINE
    
    if expansion not in quests_by_expansion:
        quests_by_expansion[expansion] = {}
    
    if quest_group not in quests_by_expansion[expansion]:
        quests_by_expansion[expansion][quest_group] = []
    
    quests_by_expansion[expansion][quest_group].append(quest)

# Extract A Realm Reborn quests
arr_quests = [quest for quest in quests_by_number.values() if quest["ExpansionName"] == expansion_mapping[0]]

# Function to order quests based on the NextMSQ path, considering QuestGroup
def order_quests_by_next_msq(quests, group=None):
    # Create a mapping from quest ID to quest
    quest_map = {quest["#"]: quest for quest in quests}
    
    # Find the starting quests (which do not appear in any NextMSQ)
    start_quests = {quest["#"] for quest in quests} - {quest["NextMSQ"] for quest in quests if quest["NextMSQ"]}

    if not start_quests:
        print(f"No starting quest found in the {expansion_mapping[0]} category for {group if group else QUEST_GROUP_MAIN_QUEST_LINE}. Skipping...")
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

# Sort the A Realm Reborn quests by group
sorted_quests_by_group = {}

# Function to validate the order of quests based on the NextMSQ field
def validate_quest_order(sorted_quests, quests_by_number):
    for i in range(len(sorted_quests) - 1):
        current_quest = sorted_quests[i]
        next_quest = sorted_quests[i + 1]

        # Validate that the current quest's NextMSQ is the next quest in the sorted list
        if current_quest["NextMSQ"] != next_quest["#"]:
            expected_next = quests_by_number.get(current_quest["NextMSQ"], {}).get("Name", "Unknown")
            print(f"❌ Order issue: '{current_quest['Name']}' (ID: {current_quest['#']}) should link to "
                  f"'{next_quest['Name']}' (ID: {next_quest['#']}), but links to '{expected_next}' instead.")

# Process each quest group
for group in QUEST_GROUPS:
    group_quests = [quest for quest in quests_by_expansion[expansion_mapping[0]].get(group, [])]
    if group_quests:  # Only process if there are quests for this group
        sorted_quests_by_group[group] = order_quests_by_next_msq(group_quests, group)
        validate_quest_order(sorted_quests_by_group[group], quests_by_number)

len_gridania = len(sorted_quests_by_group.get(QUEST_GROUP_GRIDANIA, []))
len_uldah = len(sorted_quests_by_group.get(QUEST_GROUP_ULDAH, []))
len_limsa_lominsa = len(sorted_quests_by_group.get(QUEST_GROUP_LIMSA_LOMINSA, []))
print(f"Sorted ARR quest group lengths: {QUEST_GROUP_GRIDANIA}: {len_gridania}, {QUEST_GROUP_ULDAH}: {len_uldah}, {QUEST_GROUP_LIMSA_LOMINSA}: {len_limsa_lominsa}")

# Handle the Main Quest Line
main_quest_line_quests = [quest for quest in quests_by_expansion[expansion_mapping[0]].get(QUEST_GROUP_MAIN_QUEST_LINE, [])]
if main_quest_line_quests:
    sorted_quests_by_group[QUEST_GROUP_MAIN_QUEST_LINE] = order_quests_by_next_msq(main_quest_line_quests, QUEST_GROUP_MAIN_QUEST_LINE)
    validate_quest_order(sorted_quests_by_group[QUEST_GROUP_MAIN_QUEST_LINE], quests_by_number)

print(f"Sorted ARR {QUEST_GROUP_MAIN_QUEST_LINE} quests length: {len(sorted_quests_by_group[QUEST_GROUP_MAIN_QUEST_LINE])}")

# Validation function to check the integrity of the NextMSQ chain
def validate_linked_list(starting_quests, quests_by_number):
    for start_quest_id in starting_quests:
        current_quest = quests_by_number.get(start_quest_id, None)
        
        if not current_quest:
            print(f"=> Starting quest with ID '{start_quest_id}' not found.")
            continue
        
        print(f"[Validating linked list starting from '{current_quest['Name']}' (ID: {current_quest['#']})]")
        
        while current_quest:
            next_quest_id = current_quest["NextMSQ"]
            if next_quest_id is None:
                print(f"✓ Reached the final quest in the chain: '{current_quest['Name']}' (ID: {current_quest['#']})")
                break
            
            if next_quest_id not in quests_by_number:
                print(f"❌ Validation error: '{current_quest['Name']}' (ID: {current_quest['#']}) points to non-existent NextMSQ ID: {next_quest_id}")
                break
            
            current_quest = quests_by_number[next_quest_id]

# Validate the linked list for starting quests
validate_linked_list(STARTING_QUEST_IDS, quests_by_number)

# Combine all sorted quests back into the quests_by_expansion structure
quests_by_expansion[expansion_mapping[0]] = sorted_quests_by_group

# Important: CSV uses int32 for quest IDs, but for reasons the dump makes strings so we just convert them here
def convert_quest_fields_to_numbers(quest):
    quest["#"] = int(quest["#"])
    if quest["NextMSQ"] is not None:
        quest["NextMSQ"] = int(quest["NextMSQ"])
    quest["PreviousQuests"] = [int(q) for q in quest["PreviousQuests"]]
# Convert #, NextMSQ, and PreviousQuests to numbers
for quest in quests_by_number.values():
    convert_quest_fields_to_numbers(quest)

# Convert the dictionary into the desired array format
quests_array = []
for expansion, groups in quests_by_expansion.items():
    quests_array.append({
        "name": expansion,
        "quests": groups
    })

# Save the structured data to a JSON file
with open(OUTPUT_JSON_PATH, 'w') as json_file:
    json.dump(quests_array, json_file, indent=4)

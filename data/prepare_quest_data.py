import pandas as pd
import json
import requests
import time
import argparse

from tqdm import tqdm
from io import StringIO

# For debugging
# import ipdb;
import logging
logging.basicConfig(
    level=logging.INFO,
    format="\033[1m[%(levelname)s]\033[0m ► %(message)s\n",
)

"""
    Arguments
"""

parser = argparse.ArgumentParser(description="Process quest data.")
parser.add_argument(
    "--auto-yes",
    action="store_true",
    help="Automatically assume 'yes' for all prompts.",
)
args = parser.parse_args()
auto_yes = args.auto_yes # Check if auto-yes is enabled for automation

"""
    Constants
"""

OUTPUT_JSON_PATH = "static/Quests.json"

RAW_QUESTS_CSV_URL = "https://raw.githubusercontent.com/xivapi/ffxiv-datamining/master/csv/Quest.csv"
RAW_EXVERSION_CSV_URL = "https://raw.githubusercontent.com/xivapi/ffxiv-datamining/master/csv/ExVersion.csv"
RAW_INSTANCE_CONTENT_CSV_URL = "https://raw.githubusercontent.com/xivapi/ffxiv-datamining/master/csv/InstanceContent.csv"
RAW_JOURNAL__CSV_BASE_URL = "https://raw.githubusercontent.com/xivapi/ffxiv-datamining/master/csv/quest"  # + expansion_number_to_three_digits + quest_id + '.csv'

XIV_BETA_API_SEARCH_BASE_URL = "https://beta.xivapi.com/api/1/search"
XIV_BETA_API_INSTANCE_CONTENT_BASE_URL = "https://beta.xivapi.com/api/1/sheet/ContentFinderCondition"

QUEST_GROUP_GRIDANIA = "Gridania"
QUEST_GROUP_ULDAH = "Ul'dah"
QUEST_GROUP_LIMSA_LOMINSA = "Limsa Lominsa"
QUEST_GROUP_MAIN_QUEST_LINE = "Main Quest Line"
QUEST_GROUPS = [
    QUEST_GROUP_GRIDANIA,
    QUEST_GROUP_ULDAH,
    QUEST_GROUP_LIMSA_LOMINSA,
    QUEST_GROUP_MAIN_QUEST_LINE,
]

ENVOY_TO_QUEST_GROUP = {
    66064: QUEST_GROUP_ULDAH,
    66082: QUEST_GROUP_LIMSA_LOMINSA,
    66043: QUEST_GROUP_GRIDANIA,
}

CONVERGING_QUEST_ID = 66209 # The quest where the ARR main quest line converges and starts
STARTING_QUEST_IDS = [
    # IDs for the "Close to Home" quests in Gridania, Ul'dah, and Limsa Lominsa
    65621,
    66104,
    65644,
]

""" 
    Functions: Fetching Data
"""

last_successful_folder_index = 0
def fetch_with_retries(url, max_retries=5, delay=2, params=None):
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response
            if response.status_code == 404:
                logging.info(f"Resource not found: {url} with params {params}.")
                return None
            logging.warning(
                f"Request failed with status {response.status_code} (attempt {attempt}/{max_retries})."
            )
        except requests.exceptions.RequestException as e:
            logging.warning(f"Request error on attempt {attempt}/{max_retries}: {e}")
        time.sleep(delay)
    logging.error(f"Failed to fetch: {url} after {max_retries} attempts.")
    return None

def fetch_first_journal_entry(
    quest_id,
    max_folder_number=100,
    max_retries=5,
    delay=2,
    start_from_last_success=True,
):
    global last_successful_folder_index
    start_index = last_successful_folder_index if start_from_last_success else 0

    for folder_index in range(start_index, max_folder_number + 1):
        csv_url = (
            f"{RAW_JOURNAL__CSV_BASE_URL}/{str(folder_index).zfill(3)}/{quest_id}.csv"
        )
        logging.info(f"Trying URL: {csv_url}")
        response = fetch_with_retries(csv_url, max_retries, delay)
        if response is None:
            logging.info(f"No data found at {csv_url}. Continuing...")
            continue

        try:
            csv_content = response.content.decode("utf-8")
            journal_data = pd.read_csv(StringIO(csv_content), skiprows=[0, 1])
            if not journal_data.empty:
                last_successful_folder_index = folder_index
                return journal_data.iloc[0, 2]
        except Exception as e:
            logging.warning(f"Failed to process CSV from {csv_url}: {e}")
            continue

    logging.warning(f"No journal entry found for quest ID: {quest_id}.")
    return None

def fetch_instance_content(instance_id):
    instance_url = f"{XIV_BETA_API_INSTANCE_CONTENT_BASE_URL}/{instance_id}"
    response = fetch_with_retries(instance_url)
    if response is None:
        logging.warning(f"Failed to fetch instance content for ID {instance_id}.")
        return None

    try:
        instance_data = response.json()
        fields = instance_data.get("fields", {})
        return {
            "Name": fields.get("Name", "Unknown"),
            "Image": fields.get("Image", {}).get("path_hr1", ""),
            "ContentTypeName": fields.get("ContentType", {})
            .get("fields", {})
            .get("Name", "Unknown"),
        }
    except Exception as e:
        logging.warning(f"Failed to parse instance content for ID {instance_id}: {e}")
    return None

def fetch_image_path(quest_name):
    response = fetch_with_retries(
        XIV_BETA_API_SEARCH_BASE_URL,
        params={
            "sheets": "Quest",
            "query": f'Name~"{quest_name}"',
            "fields": "Icon,Name",
        },
    )
    if response is None:
        logging.warning(f"Failed to fetch image for quest '{quest_name}'.")
        return None

    try:
        data = response.json()
        if data.get("results"):
            return data["results"][0]["fields"]["Icon"]["path_hr1"]
    except Exception as e:
        logging.warning(f"Failed to parse image data for quest '{quest_name}': {e}")
    return None

""" 
    Functions: Data frame processing
"""

def load_instance_content_mapping():
    response = requests.get(RAW_INSTANCE_CONTENT_CSV_URL)
    if response.status_code == 200:
        csv_content = response.content.decode("utf-8")
        exversion_data = pd.read_csv(StringIO(csv_content), skiprows=[0, 2])
        # Create a mapping of index to expansion name
        return {row["#"]: row["Order"] for _, row in exversion_data.iterrows()}
    else:
        logging.warning(
            f"Failed to download InstanceContent.csv. Status code: {response.status_code}"
        )
        exit()

def load_expansion_mapping():
    response = requests.get(RAW_EXVERSION_CSV_URL)
    if response.status_code == 200:
        csv_content = response.content.decode("utf-8")
        exversion_data = pd.read_csv(StringIO(csv_content), skiprows=[0, 2])
        # Create a mapping of index to expansion name
        return {row["#"]: row["Name"] for _, row in exversion_data.iterrows()}
    else:
        logging.warning(
            f"Failed to download ExVersion.csv. Status code: {response.status_code}"
        )
        exit()

def pd_get_previous_quests(row):
    return [
        int(row[f"PreviousQuest[{i}]"])
        for i in range(4)
        if not pd.isna(row[f"PreviousQuest[{i}]"])
        and str(row[f"PreviousQuest[{i}]"]).strip() != "0"
    ]
    
def pd_resolve_unlocks_by_row(row):
    unlocks = []

    for col_idx in range(len(row)):
        instruction_column = f"Script{{Instruction}}[{col_idx}]"
        arg_column = f"Script{{Arg}}[{col_idx}]"

        # Ensure both columns exist in the row
        if instruction_column in row and arg_column in row:
            instruction_value = row[instruction_column]
            arg_value = row[arg_column]

            # Check for "INSTANCEDUNGEON" in the instruction column
            if pd.notna(instruction_value) and "INSTANCEDUNGEON" in str(
                instruction_value
            ):
                # Validate instance ID (non-empty, non-zero)
                if pd.notna(arg_value) and str(arg_value).strip() != "0":
                    logging.info(
                        f"Found unlock instruction: {instruction_value} with arg: {arg_value}"
                    )

                    # Lookup the final ID using the mapping
                    final_id = instance_content_mapping.get(int(arg_value))
                    if final_id:
                        instance_details = fetch_instance_content(final_id)
                        if instance_details:
                            logging.info(
                                f"Resolved instance ID {final_id} to {instance_details['Name']}"
                            )
                            unlocks.append(instance_details)
                        else:
                            logging.warning(
                                f"Failed to fetch instance details for ID {final_id}."
                            )
                    else:
                        logging.warning(
                            f"Instance ID {arg_value} not found in instance content mapping."
                        )

    return unlocks
     
""" 
    Functions: Post-processing utilities
""" 

def get_expansion_name(expansion_index, expansion_mapping):
    return expansion_mapping.get(expansion_index, "Unknown")

def order_quests_by_next_msq(quests, group=None):
    # Create a mapping from quest ID to quest
    quest_map = {quest["#"]: quest for quest in quests}

    # Find the starting quests (which do not appear in any NextMSQ)
    start_quests = {quest["#"] for quest in quests} - {
        quest["NextMSQ"] for quest in quests if quest["NextMSQ"]
    }

    if not start_quests:
        logging.INFO(
            f"No starting quest found in the {expansion_mapping[0]} category for {group if group else QUEST_GROUP_MAIN_QUEST_LINE}. Skipping..."
        )
        return []

    # Track processed quests to avoid duplicates
    processed_quests = set()

    # There might be multiple starting quests, so we handle each path separately
    sorted_quests = []
    for start_quest_id in start_quests:
        current_quest_id = start_quest_id
        while current_quest_id:
            if current_quest_id not in quest_map:
                logging.warning(
                    f"Quest ID {current_quest_id} not found in quest_map. Skipping."
                )
                break

            if current_quest_id in processed_quests:
                logging.info(f"Skipping duplicate quest ID {current_quest_id}.")
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

def convert_quest_fields_to_numbers(quest):
    # Important: CSV uses int32 for quest IDs, but for reasons the dump makes strings so we just convert them here
    quest["#"] = int(quest["#"])
    if quest["NextMSQ"] is not None:
        quest["NextMSQ"] = int(quest["NextMSQ"])
    quest["PreviousQuests"] = [int(q) for q in quest["PreviousQuests"]]
    
    
"""
    Functions: Validation
"""

# Function to validate the order of quests based on the NextMSQ field
def validate_quest_order(sorted_quests, quests_by_number):
    for i in range(len(sorted_quests) - 1):
        current_quest = sorted_quests[i]
        next_quest = sorted_quests[i + 1]

        # Validate that the current quest's NextMSQ is the next quest in the sorted list
        if current_quest["NextMSQ"] != next_quest["#"]:
            expected_next = quests_by_number.get(current_quest["NextMSQ"], {}).get(
                "Name", "Unknown"
            )
            logging.warning(
                f"❌ Order issue: '{current_quest['Name']}' (ID: {current_quest['#']}) should link to "
                f"'{next_quest['Name']}' (ID: {next_quest['#']}), but links to '{expected_next}' instead."
            )
            
# Validation function to check the integrity of the NextMSQ chain
def validate_linked_list(starting_quests, quests_by_number):
    for start_quest_id in starting_quests:
        current_quest = quests_by_number.get(start_quest_id, None)
        if not current_quest:
            logging.info(f"=> Starting quest with ID '{start_quest_id}' not found.")
            continue
        logging.info(
            f"[Validating linked list starting from '{current_quest['Name']}' (ID: {current_quest['#']})]"
        )
        while current_quest:
            next_quest_id = current_quest["NextMSQ"]
            if next_quest_id is None:
                logging.info(
                    f"✓ Reached the final quest in the chain: '{current_quest['Name']}' (ID: {current_quest['#']})"
                )
                break
            if next_quest_id not in quests_by_number:
                logging.warning(
                    f"❌ Validation error: '{current_quest['Name']}' (ID: {current_quest['#']}) points to non-existent NextMSQ ID: {next_quest_id}"
                )
                break
            current_quest = quests_by_number[next_quest_id]

"""
    Main Script
"""

# Index -> Expansion Name mapping
expansion_mapping = load_expansion_mapping()
instance_content_mapping = load_instance_content_mapping()

# Raw CSV URL for the Quest data
response = requests.get(RAW_QUESTS_CSV_URL)
if response.status_code == 200:
    csv_content = response.content.decode("utf-8")
    logging.info("Quest.csv downloaded successfully.")
else:
    logging.fatal(f"Failed to download Quest.csv. Status code: {response.status_code}")
    exit()

# Load the CSV content and include the first 1523 columns (including the penultimate column)
quest_data = pd.read_csv(StringIO(csv_content), skiprows=[0, 2], low_memory=False)

# Drop rows where 'Name' column has NaN values
quest_data = quest_data.dropna(subset=["Name"])

# Filter to keep rows where EventIconType is 3 which represents Main Scenario Quests
filtered_data = quest_data[quest_data["EventIconType"] == 3]

# Access the penultimate column by its index (-2) and filter out obsolete quests
filtered_data = filtered_data[filtered_data.iloc[:, -2] == False]

# Prompt user if they want to fetch images
fetch_images = (
    True
    if auto_yes
    else input("Do you want to fetch images? (yes/no): ").strip().lower() == "yes"
)

# Prompt user if they want to fetch journal entries
fetch_journal_entries = (
    True
    if auto_yes
    else input("Do you want to fetch journal entries? (yes/no): ").strip().lower()
    == "yes"
)

# Prompt user if they want to fetch unlocks
fetch_unlocks = (
    True
    if auto_yes
    else input("Do you want to fetch unlocks? (yes/no): ").strip().lower() == "yes"
)

# Build quests by number
# Structure:
# {
#   66209: {quest},
#   ...
# }
quests_by_number = {}
with tqdm(total=len(filtered_data), desc="Processing Quests", ncols=100) as pbar:
    for _, row in filtered_data.iterrows():
        quest_name = row["Name"]
        quest_id = row["Id"]
        quest_number = row["#"]
        quest_icon_type = row["EventIconType"]
        quest_group = None
        expansion_name = get_expansion_name(row["Expansion"], expansion_mapping)

        # Initialize the Unlocks array
        unlocks = []

        if fetch_unlocks:
            # Search for instance dungeons unlocked by this quest
            unlocks = pd_resolve_unlocks_by_row(row)

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
            "PreviousQuests": pd_get_previous_quests(row),
            "NextMSQ": None,  # Initialize as None, to be filled later
            "QuestGroup": quest_group,
            "Image": image_path,
            "Unlocks": unlocks,  # Add the Unlocks property
        }
        quests_by_number[quest_number] = quest

        pbar.update(1)

## Calculate ARR quest groups based on quests that lead to the envoy quests
envoy_quests = [quests_by_number[quest_number] for quest_number in ENVOY_TO_QUEST_GROUP.keys() if quest_number in quests_by_number]
if not envoy_quests:
    raise ValueError("No envoy quests found in quests by number.")
for envoy_quest in envoy_quests: 
    quest_number = envoy_quest["#"] 
    group = ENVOY_TO_QUEST_GROUP.get(quest_number)
    logging.info(
        f"\nAssigning quest group '{group}' by traversing backwards from '{envoy_quest['Name']}' with ID: {envoy_quest['#']}"
    )
    current_quest = envoy_quest
    while current_quest is not None:
        logging.info(
            f"Assigning '{group}' to quest: {current_quest['Name']}, ID: {current_quest['#']}"
        )
        # Assign the group to the current quest
        quests_by_number[current_quest["#"]]["QuestGroup"] = group
        # Find the previous quests
        previous_quest_ids = current_quest["PreviousQuests"]
        # Move to the first available previous quest that is also an MSQ (EventIconType == 3)
        current_quest = None
        for prev_id in previous_quest_ids:
            if prev_id in quests_by_number:
                potential_quest = quests_by_number[prev_id]
                if potential_quest.get("EventIconType") == 3:  # Check if it's an MSQ
                    current_quest = potential_quest
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
    quest_id: quest
    for quest_id, quest in quests_by_number.items()
    if quest["NextMSQ"] or quest_id == max_quest_id
}

logging.info(f"After filtering no NextMSQ, {len(quests_by_number)} quests remain.")

# Organize the data into the desired structure with correct MSQ order
quests_by_expansion = {}
# Structure:
# {
#   "A Realm Reborn": {
#       "Gridania": [quests],
#       "Ul'dah": [quests],
#       "Limsa Lominsa": [quests],
#       "Main Quest Line": [quests]
#   },
#   "Heavensward": {
#       "Main Quest Line": [quests]
#   },
#   ... and so on
# }
#
for quest in quests_by_number.values():
    expansion = quest["ExpansionName"]
    quest_group = (
        quest["QuestGroup"] if quest["QuestGroup"] else QUEST_GROUP_MAIN_QUEST_LINE
    )
    if expansion not in quests_by_expansion:
        quests_by_expansion[expansion] = {}
    if quest_group not in quests_by_expansion[expansion]:
        quests_by_expansion[expansion][quest_group] = []
    quests_by_expansion[expansion][quest_group].append(quest)

# Filter out unvisited nodes in the ARR main quest line
main_quest_line = quests_by_expansion[expansion_mapping[0]][QUEST_GROUP_MAIN_QUEST_LINE]
main_quest_line_len = len(main_quest_line)
quest_map = {quest["#"]: quest for quest in main_quest_line}

# Traverse the linked list starting at 66209
visited = set()
stack = [CONVERGING_QUEST_ID]
while stack:
    current_id = stack.pop()
    if current_id in visited:
        continue
    visited.add(current_id)

    current_quest = quest_map.get(current_id)
    if not current_quest:
        continue

    next_id = current_quest.get("NextMSQ")
    # Stop traversal if the next quest ID is missing
    if next_id and next_id in quest_map:
        stack.append(next_id)

# Filter the main quest line to keep only visited quests
main_quest_line = [quest for quest in main_quest_line if quest["#"] in visited]
quests_by_expansion[expansion_mapping[0]][QUEST_GROUP_MAIN_QUEST_LINE] = main_quest_line
logging.info(
    f"After filtering unvisited nodes, {len(main_quest_line)}/{main_quest_line_len} quests remain in the ARR main quest line."
)

# Sort the A Realm Reborn quests by group
sorted_quests_by_group = {}

# Process each quest group
for group in QUEST_GROUPS:
    group_quests = [
        quest for quest in quests_by_expansion[expansion_mapping[0]].get(group, [])
    ]
    if group_quests:  # Only process if there are quests for this group
        sorted_quests_by_group[group] = order_quests_by_next_msq(group_quests, group)
        validate_quest_order(sorted_quests_by_group[group], quests_by_number)

len_gridania = len(sorted_quests_by_group.get(QUEST_GROUP_GRIDANIA, []))
len_uldah = len(sorted_quests_by_group.get(QUEST_GROUP_ULDAH, []))
len_limsa_lominsa = len(sorted_quests_by_group.get(QUEST_GROUP_LIMSA_LOMINSA, []))
logging.info(
    f"Sorted ARR quest group lengths: {QUEST_GROUP_GRIDANIA}: {len_gridania}, {QUEST_GROUP_ULDAH}: {len_uldah}, {QUEST_GROUP_LIMSA_LOMINSA}: {len_limsa_lominsa}"
)

# Handle the Main Quest Line
main_quest_line_quests = [
    quest
    for quest in quests_by_expansion[expansion_mapping[0]].get(
        QUEST_GROUP_MAIN_QUEST_LINE, []
    )
]
if main_quest_line_quests:
    sorted_quests_by_group[QUEST_GROUP_MAIN_QUEST_LINE] = order_quests_by_next_msq(
        main_quest_line_quests, QUEST_GROUP_MAIN_QUEST_LINE
    )
    validate_quest_order(
        sorted_quests_by_group[QUEST_GROUP_MAIN_QUEST_LINE], quests_by_number
    )

logging.info(
    f"Sorted ARR {QUEST_GROUP_MAIN_QUEST_LINE} quests length: {len(sorted_quests_by_group[QUEST_GROUP_MAIN_QUEST_LINE])}"
)

# Validate the linked list for starting quests
validate_linked_list(STARTING_QUEST_IDS, quests_by_number)

# Combine all sorted quests back into the quests_by_expansion structure
quests_by_expansion[expansion_mapping[0]] = sorted_quests_by_group

# Convert #, NextMSQ, and PreviousQuests to numbers
for quest in quests_by_number.values():
    convert_quest_fields_to_numbers(quest)

# Convert the dictionary into the desired array format
quests_array = []
for expansion, groups in quests_by_expansion.items():
    quests_array.append({"name": expansion, "quests": groups})

# Save the structured data to a JSON file
with open(OUTPUT_JSON_PATH, "w") as json_file:
    json.dump(quests_array, json_file, indent=4)

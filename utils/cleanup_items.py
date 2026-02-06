import json
import os

# Path relative to where you run the script (project root)
FILE_PATH = os.path.join("data", "items.json")

def remove_duplicates():
    if not os.path.exists(FILE_PATH):
        print(f"File not found: {FILE_PATH}")
        return

    print(f"Scanning {FILE_PATH}...")
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)

    seen_ids = set()
    unique_items = []
    duplicates_count = 0

    for item in items:
        item_id = item.get("id")
        if item_id and item_id in seen_ids:
            duplicates_count += 1
        else:
            if item_id:
                seen_ids.add(item_id)
            unique_items.append(item)

    if duplicates_count > 0:
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(unique_items, f, indent=2)
        print(f"Successfully removed {duplicates_count} duplicate items.")
    else:
        print("No duplicates found.")

if __name__ == "__main__":
    remove_duplicates()
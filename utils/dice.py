import random
import re

def roll_dice(dice_str: str) -> int:
    # Converts a dice notation string (e.g., "2d6+3", "1d10", "5") into a random integer result.
    dice_str = str(dice_str).lower().strip()

    # Case 1: The string is just a number
    if dice_str.isdigit():
        return int(dice_str)

    # Case 2: The string is in dice notation (e.g., "1d6", "2d10+3")
    match = re.match(r"(\d+)d(\d+)\s*([+-])?\s*(\d+)?", dice_str)
    if match:
        num_dice = int(match.group(1))
        die_faces = int(match.group(2))
        
        # Roll the dice
        total = sum(random.randint(1, die_faces) for _ in range(num_dice))
        
        # Add or subtract modifier if it exists
        if match.group(3) and match.group(4):
            operator = match.group(3)
            modifier = int(match.group(4))
            if operator == "+":
                total += modifier
            elif operator == "-":
                total -= modifier
        
        return total

    # Fallback for unrecognized format
    return 1

def parse_and_roll_loot(loot_str: str) -> tuple[str, int, str, int, str]:
    """Parses a loot string into name, qty, qty_str, decay_val, decay_str."""
    qty_str = "1"
    name = loot_str.strip()
    
    # 1. Parse Quantity prefix "x..."
    match_qty = re.match(r"^x(\d+d\d+[+\-]?\d*|\d+)\s+(.*)", name, re.IGNORECASE)
    if match_qty:
        qty_str = match_qty.group(1)
        name = match_qty.group(2).strip()
    
    qty = roll_dice(qty_str)
    
    # 2. Parse Decay suffix "(... levels of decay)"
    decay_val = 0
    decay_str = ""
    match_decay = re.search(r"\(([\dd+\-\s]+)\s+levels? of decay\)", name, re.IGNORECASE)
    if match_decay:
        decay_str = match_decay.group(1).strip()
        decay_val = roll_dice(decay_str)
        name = name.replace(match_decay.group(0), "").strip()
        
    return name, qty, qty_str, decay_val, decay_str
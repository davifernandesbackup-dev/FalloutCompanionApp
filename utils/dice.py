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
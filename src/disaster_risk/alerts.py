"""Display levels (green / amber / red) for model outputs.

These are display rules for the dashboard, not measured values. The only numbers
that come from the training data are the class rules in config.py. The two
thresholds below are display settings and can be changed here.
"""

# Flood: the class rule is probability >= 0.5 (config.FLOOD_THRESHOLD). Amber marks
# probabilities just below it, where the class is "No flood" but close to the rule.
FLOOD_NEAR_THRESHOLD = 0.40

# Earthquake: level follows the most probable class (Low green, Medium amber,
# High red). A High-class probability at or above this value raises the level to at
# least amber, because the saved model finds only 6 of 988 High test events.
EQ_HIGH_FLAG_PROBABILITY = 0.05

LEVEL_NAMES = {"green": "No flag", "amber": "Elevated", "red": "High"}


def flood_level(p_flood: float) -> dict:
    if p_flood >= 0.5:
        level, label = "red", "Flood class"
    elif p_flood >= FLOOD_NEAR_THRESHOLD:
        level, label = "amber", "No-flood class, near the 0.5 rule"
    else:
        level, label = "green", "No-flood class"
    return {"level": level, "label": label, "flagged": level != "green"}


def earthquake_level(probs: dict) -> dict:
    top = max(probs, key=probs.get)
    level = {"Low": "green", "Medium": "amber", "High": "red"}[top]
    label = f"{top} class most probable"
    if level == "green" and probs["High"] >= EQ_HIGH_FLAG_PROBABILITY:
        level, label = "amber", f"Low class most probable, High-class probability at or above {EQ_HIGH_FLAG_PROBABILITY:.2f}"
    return {"level": level, "label": label, "top": top, "flagged": level != "green"}


# Notification to departments. Delivery is not connected; a notification is only recorded. A notification is prepared only for level High.
# Department names are placeholders; replace them with the real recipients before any delivery is connected.
DISPATCH_LEVEL = "red"
DEPARTMENTS = {"flood": "Flood response department", "earthquake": "Earthquake response department"}
CHANNELS = ["SMS", "Email", "Push notification"]


def notification_message(row: dict) -> str:
    """Text a department would receive for a saved High flag. Built only from the saved calculation."""
    if row["model"] == "flood":
        p = row["probabilities"]["Flood class"]
        text = f"HIGH flag, flood model: flood class, probability {p:.4f} (class rule 0.5 or higher)."
        pl = row.get("place")
        if pl:
            text += f" Place: {pl.get('name') or 'not named'} ({pl['latitude']:.4f}, {pl['longitude']:.4f})."
    else:
        i, pr = row["inputs"], row["probabilities"]
        text = (f"HIGH flag, earthquake model: {row['result_class']} class most probable. Longitude {i['longitude']:.4f}, "
                f"latitude {i['latitude']:.4f}, depth {i['depth']:.1f} km. "
                f"Low {pr['Low']:.4f}, Medium {pr['Medium']:.4f}, High {pr['High']:.4f}.")
    return text + f" Calculated {row['created']}. Model output on historical data; please verify."

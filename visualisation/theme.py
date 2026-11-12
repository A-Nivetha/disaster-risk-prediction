"""Colours shared by the dashboard and the figures. Green / amber / red mean severity and flag levels only."""
BG, CARD, BORDER = "#0B1220", "#131F35", "#2A3A58"
TEXT, MUTED = "#F1F5F9", "#B6C2D4"
BLUE = "#3B82F6"
SEV = {"Low": "#22C55E", "Medium": "#F59E0B", "High": "#EF4444"}
LEVEL = {"green": "#22C55E", "amber": "#F59E0B", "red": "#EF4444"}
LEVEL_TEXT = {"green": "#4ADE80", "amber": "#FBBF24", "red": "#F87171", "blue": "#93C5FD", "teal": "#5EEAD4"}
KPI = {**LEVEL, "blue": BLUE, "teal": "#14B8A6"}

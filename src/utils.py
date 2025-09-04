import re

def parse_game_events(text: str):
    events = []
    # NPC
    for match in re.finditer(r"\[NPC:(\w+)\]\s*\"?([^\"\]]+)", text):
        events.append({
            "type": "npc_speak",
            "name": match.group(1),
            "text": match.group(2).strip()
        })
    clean_text = re.sub(r"\[NPC:[^\]]+\][^\n]*", "", text)
    # CLUE, QUEST, CHOICE... add more if needed
    if clean_text.strip():
        events.append({"type": "narrative", "text": clean_text.strip()})
    return events
ACTIONS = ("WATCH", "PREPARE", "ALERT", "ESCALATE")


def stub_action(minute: int) -> str:
    # Placeholder until decide.py is built (P9): always WATCH
    return "WATCH"

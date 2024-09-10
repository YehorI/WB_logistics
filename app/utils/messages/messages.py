import yaml

from pathlib import Path

MESSAGES_PATH = Path(__file__).parent / "messages.yaml"

def get_message_text_by_key(
    key: str,
    path: Path | str=MESSAGES_PATH,
):
    with open(path, "rt", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    return data[key]

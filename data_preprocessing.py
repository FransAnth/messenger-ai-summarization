import json
from datetime import datetime, timezone
from pathlib import Path

source_path = Path("messages/inbox")


def main():
    final_data = {}

    # 1. Check if source path exists to prevent crashes
    if not source_path.exists():
        print(f"❌ Error: Source path '{source_path}' does not exist.")
        return

    for item in source_path.iterdir():
        if item.is_dir():
            print(f"📁 Processing folder: {item.name}")

            conversation_data = {}
            for content in item.iterdir():
                if content.is_file() and content.suffix == ".json":
                    # Safe reading with UTF-8 encoding
                    with open(content, "r", encoding="utf-8") as file:
                        messages_info = json.load(file)

                    messages_data = []
                    # Fallback to empty list if "messages" key is missing
                    for message in messages_info.get("messages", []):
                        content_text = message.get("content")

                        if content_text:
                            # Convert timestamp safely
                            dt_utc = datetime.fromtimestamp(
                                message.get("timestamp_ms", 0) / 1000, tz=timezone.utc
                            )

                            participant_message_data = {
                                "sender_name": message.get("sender_name"),
                                "content": content_text,
                                "timestamp": dt_utc.strftime(
                                    "%B %d, %Y at %I:%M:%S %p UTC"
                                ),
                            }
                            # Fast O(1) appending
                            messages_data.append(participant_message_data)

                    # Reverse the list ONCE at the end to get oldest to newest order
                    messages_data.reverse()

                    conversation_data = {
                        # "participants": messages_info.get("participants", []),
                        "messages": messages_data,
                    }

            final_data[item.name] = conversation_data

    # Save to JSON safely supporting emojis/foreign characters
    output_file = Path("messages_data.json")
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(final_data, file, indent=4, ensure_ascii=False)

    print(f"\n✅ Done! Saved consolidated data to {output_file.resolve()}")


if __name__ == "__main__":
    main()

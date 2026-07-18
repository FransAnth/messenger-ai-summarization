import csv
import json
import os
import time  # Added for retry delays
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

# Assuming system_prompt is defined in a separate file named prompt.py
from prompt import system_prompt

load_dotenv()

# Grab the API Key from the environment
api_key = os.environ.get("GEMINI_API_KEY")


def ask_gemini(model_name: str, system_prompt: str, prompt: str) -> str:
    """
    Sends a prompt to the Gemini API with a system prompt and returns only the text.
    """
    client = genai.Client(api_key=api_key)

    # Package the system instruction and ENFORCE JSON output
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        response_mime_type="application/json",  # Forces strict JSON format
    )

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )
        return response.text

    except APIError as e:
        raise RuntimeError(f"Gemini API Error [{e.code}]: {e.message}") from e
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}") from e


def main():
    source_file = Path("messages_data.json")
    output_csv = Path("analysis_results.csv")
    output_json = Path("analysis_results.json")

    # Retry configuration constants
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 2  # seconds to wait on first failure

    # Check if the file actually exists before trying to read it
    if not source_file.exists():
        print(
            f"❌ Error: '{source_file}' not found. Did you run the consolidation script first?"
        )
        return

    # Open the file and use json.load() with UTF-8 encoding
    with open(source_file, "r", encoding="utf-8") as file:
        conversations = json.load(file)

    # List to collect enriched conversations for the master JSON output
    analyzed_conversations_list = []

    # Open the CSV file for writing
    with open(output_csv, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)

        # Write the CSV headers
        writer.writerow(
            [
                "Conversation_Name",
                "Category",
                "Summary",
                "User_Behavior",
                "Company_Performance",
                "Next_Best_Action",
            ]
        )

        print(f"📊 Starting analysis of {len(conversations)} conversations...")

        for conversation in conversations:
            conv_name = conversation.get("name", "Unknown")
            print(f"\n🚀 Analyzing conversation: {conv_name}...")

            # Convert the conversation dictionary back to a formatted string for the AI
            chat_history_str = json.dumps(conversation, indent=2, ensure_ascii=False)
            input_prompt = f"Analyze this conversation: \n\n{chat_history_str}"

            # Retry loop block
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    # Call Gemini
                    response_text = ask_gemini(
                        model_name="gemini-3.1-flash-lite",
                        system_prompt=system_prompt,
                        prompt=input_prompt,
                    )

                    # Parse the returned JSON string into a Python dictionary
                    ai_data = json.loads(response_text)
                    analytics = ai_data.get("analytics", {})

                    # 1. Write the row to the CSV
                    writer.writerow(
                        [
                            conv_name,
                            ai_data.get("category", ""),
                            ai_data.get("summary", ""),
                            analytics.get("user_behavior", ""),
                            analytics.get("company_performance", ""),
                            analytics.get("next_best_action", ""),
                        ]
                    )

                    # 2. Prepare the data for the new JSON file
                    enriched_conversation = conversation.copy()
                    enriched_conversation["analysis"] = {
                        "category": ai_data.get("category", ""),
                        "summary": ai_data.get("summary", ""),
                        "analytics": analytics,
                    }

                    analyzed_conversations_list.append(enriched_conversation)
                    print(f"✅ Successfully analyzed and tracked '{conv_name}'.")

                    # Break out of the retry loop since the block completed successfully
                    break

                except (RuntimeError, json.JSONDecodeError) as e:
                    print(
                        f"⚠️ Attempt {attempt}/{MAX_RETRIES} failed for '{conv_name}': {e}"
                    )

                    if attempt < MAX_RETRIES:
                        # Exponential backoff: waits 2s, then 4s, etc.
                        sleep_time = INITIAL_BACKOFF * attempt
                        print(f"   Retrying in {sleep_time} seconds...")
                        time.sleep(sleep_time)
                    else:
                        print(
                            f"❌ Max retries reached. Skipping conversation '{conv_name}'."
                        )

    # Save the complete tracking data to the final JSON file
    print(f"\n💾 Saving master records to JSON format...")
    with open(output_json, "w", encoding="utf-8") as json_file:
        json.dump(analyzed_conversations_list, json_file, indent=2, ensure_ascii=False)

    print(f"\n🎉 All done!")
    print(f"   - CSV saved to: {output_csv}")
    print(f"   - JSON (with full conversation history) saved to: {output_json}")


if __name__ == "__main__":
    main()

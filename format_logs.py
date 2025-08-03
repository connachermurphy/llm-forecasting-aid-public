import datetime
import json
import subprocess
import sys
import tempfile


def extract_date(timestamp):
    """Extract just the date from a timestamp string"""
    dt = datetime.datetime.fromisoformat(timestamp)
    return dt.strftime("%Y-%m-%d")


def extract_time(timestamp):
    """Extract just the time from a timestamp string"""
    # Parse the ISO timestamp
    dt = datetime.datetime.fromisoformat(timestamp)

    # Return just the time as HH:MM:SS
    return dt.strftime("%H:%M:%S")


def extract_timezone(timestamp):
    """Extract just the timezone from a timestamp string"""
    dt = datetime.datetime.fromisoformat(timestamp)
    return dt.strftime("%Z")


def load_logs(session_id):
    logs = []

    # Keep logs with appropriate session_id
    with open("logs/chat_logs.jsonl") as f:
        for line in f:
            log = json.loads(line)
            if log["session_id"] == session_id:
                logs.append(log)

    # Sort by timestamp
    logs = sorted(logs, key=lambda x: x["timestamp"])
    return logs


def format_message(who, timestamp, message):
    formatted_message = f"""
#showybox(
    breakable: true,
    title:[_{who} at {extract_time(timestamp)}_],
)[
    {message}
]
"""
    return formatted_message


def generate_typst_content(session_id):
    typst_content = """
= LLM Forecasting Aid (excessively preliminary)

#import "@preview/showybox:2.0.4": showybox
"""

    logs = load_logs(session_id)

    # Add first timestamp to typst file
    first_timestamp = logs[0]["timestamp"]

    typst_content += f"""
Conversation started at {extract_time(first_timestamp)}
{extract_timezone(first_timestamp)}
on {extract_date(first_timestamp)}

Session ID: `{session_id}`

"""

    for log in logs:
        typst_content += format_message("User", log["timestamp"], log["user_message"])
        typst_content += format_message(
            "Assistant", log["timestamp"], log["assistant_response"]
        )
    return typst_content


def main():
    if len(sys.argv) < 2:
        print("Usage: python format_logs.py <session_id> [output_path]")
        return

    session_id = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    typst_content = generate_typst_content(session_id)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".typ", delete=False, encoding="utf-8"
    ) as f:
        typst_file = f.name
        f.write(typst_content)

    try:
        result = subprocess.run(
            ["typst", "compile", typst_file, output_path],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"PDF generated at {output_path}")
        else:
            print(f"Error generating PDF: {result.stderr}")
            return

    except FileNotFoundError:
        print("Error: typst not found. Please install typst from https://typst.app/")
        return


if __name__ == "__main__":
    main()

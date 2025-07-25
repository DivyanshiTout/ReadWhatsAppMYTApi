# from flask import Flask, request, jsonify

# app = Flask(__name__)

# @app.route('/webhook', methods=['POST'])
# def webhook():
#     data = request.json
#     print("📥 New Message:", data)

#     # Get conversation ID (e.g., @c.us or @g.us)
#     conversation_id = data.get("conversation", "")
#     conversation_name = data.get("conversation_name", "")
#     message_text = data.get("message", {}).get("text", "")

#     # Detect group vs. personal
#     if conversation_id.endswith("@g.us"):
#         print("✅ It’s a group message!")
#         print("Group name:", conversation_name)
#     else:
#         print("📩 It’s an individual chat message!")
#         user_name = data.get("user", {}).get("name", "")
#         print("User name:", user_name)

#     print("Message text:", message_text)

#     return jsonify({"status": "received"}), 200

# if __name__ == '__main__':
#     app.run(port=5000)



from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("📥 New Message Received:", json.dumps(data, indent=2))

    # Extract basic information
    conversation_id = data.get("conversation", "")
    conversation_name = data.get("conversation_name", "unknown_chat").strip() or "unknown_chat"
    message_data_dict = data.get("message", {})
    message_type_content = message_data_dict.get("type", "")
    message_text = message_data_dict.get("text", "") if message_type_content == "text" else ""
    image_url = message_data_dict.get("url", "") if message_type_content == "image" else ""

    timestamp = data.get("timestamp", int(datetime.now().timestamp()))
    readable_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    # Detect message type (group/personal)
    chat_type = "group" if conversation_id.endswith("@g.us") else "personal"
    user_name = data.get("user", {}).get("name", "")

    # Handle quoted message (for text type only in this version)
    quoted = data.get("quoted")
    quoted_messages = []
    merged_message = message_text

    if quoted:
        quoted_text = quoted.get("text", "")
        if quoted_text:
            quoted_messages.append(quoted_text)
            merged_message = quoted_text + " | " + merged_message

    # Prepare single message data
    message_data = {
        "conversation_id": conversation_id,
        "conversation_name": conversation_name,
        "chat_type": chat_type,
        "user_name": user_name,
        "message_type": message_type_content,
        "message_text": message_text if message_text else None,
        "image_url": image_url if image_url else None,
        "quoted_messages": quoted_messages if quoted_messages else None,
        "merged_message": merged_message if merged_message else None,
        "timestamp": timestamp,
        "origin_time": readable_time
    }

    # Save message data into JSON file
    save_message(conversation_name, message_data)

    return jsonify({"status": "received"}), 200


@app.route('/messages', methods=['GET'])
def get_all_messages():
    output_folder = "messages"
    all_messages = []

    if not os.path.exists(output_folder):
        return jsonify({"messages": [], "note": "No messages folder found"}), 200

    for filename in os.listdir(output_folder):
        if filename.endswith(".json"):
            file_path = os.path.join(output_folder, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    all_messages.extend(data)
                except json.JSONDecodeError:
                    print(f"⚠️ Could not decode JSON in file: {file_path}")

    return jsonify({"messages": all_messages}), 200



def save_message(conversation_name, message_data):
    output_folder = "messages"
    os.makedirs(output_folder, exist_ok=True)

    # File name: e.g., tips_testing.json
    safe_name = conversation_name.replace(" ", "_").lower()
    file_path = os.path.join(output_folder, f"{safe_name}.json")

    # Load existing messages if file exists
    if os.path.isfile(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    # Add new message
    existing_data.append(message_data)

    # Save all messages back
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=4, ensure_ascii=False)

    print(f"✅ Message saved to {file_path}")


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use Render's assigned port or fallback to 5000
    app.run(host='0.0.0.0', port=port, debug=False)  

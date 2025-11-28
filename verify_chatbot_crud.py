import requests
import json
import uuid

BASE_URL = "http://localhost:8000/api/v1/chatbots"

def test_create_chatbot():
    print("Testing Create Chatbot...")
    data = {
        "name": "Test Chatbot",
        "model_name": "gemini-pro",
        "llm_config": {"temperature": 0.7}
    }
    response = requests.post(BASE_URL + "/", json=data)
    if response.status_code == 200:
        print("Create Chatbot: SUCCESS")
        return response.json()
    else:
        print(f"Create Chatbot: FAILED ({response.status_code})")
        print(response.text)
        return None

def test_get_chatbots():
    print("\nTesting Get Chatbots...")
    response = requests.get(BASE_URL + "/")
    if response.status_code == 200:
        print("Get Chatbots: SUCCESS")
        print(f"Count: {len(response.json())}")
    else:
        print(f"Get Chatbots: FAILED ({response.status_code})")
        print(response.text)

def test_get_chatbot(chatbot_id):
    print(f"\nTesting Get Chatbot ({chatbot_id})...")
    response = requests.get(f"{BASE_URL}/{chatbot_id}")
    if response.status_code == 200:
        print("Get Chatbot: SUCCESS")
    else:
        print(f"Get Chatbot: FAILED ({response.status_code})")
        print(response.text)

def test_update_chatbot(chatbot_id):
    print(f"\nTesting Update Chatbot ({chatbot_id})...")
    data = {
        "name": "Updated Chatbot Name"
    }
    response = requests.put(f"{BASE_URL}/{chatbot_id}", json=data)
    if response.status_code == 200:
        print("Update Chatbot: SUCCESS")
        print(f"New Name: {response.json()['name']}")
    else:
        print(f"Update Chatbot: FAILED ({response.status_code})")
        print(response.text)

def test_delete_chatbot(chatbot_id):
    print(f"\nTesting Delete Chatbot ({chatbot_id})...")
    response = requests.delete(f"{BASE_URL}/{chatbot_id}")
    if response.status_code == 200:
        print("Delete Chatbot: SUCCESS")
    else:
        print(f"Delete Chatbot: FAILED ({response.status_code})")
        print(response.text)

if __name__ == "__main__":
    chatbot = test_create_chatbot()
    if chatbot:
        chatbot_id = chatbot['id']
        test_get_chatbots()
        test_get_chatbot(chatbot_id)
        test_update_chatbot(chatbot_id)
        test_delete_chatbot(chatbot_id)

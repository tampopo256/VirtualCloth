import requests

access_token = 'YOUR_OAUTH_ACCESS_TOKEN'

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

data = {
    "topic": "My Zoom Meeting",
    "type": 1,  # Instant Meeting
    "settings": {
        "host_video": True,
        "participant_video": True
    }
}

response = requests.post(
    'https://api.zoom.us/v2/users/me/meetings',
    headers=headers,
    json=data
)

print(response.status_code)
print(response.json())

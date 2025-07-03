import json
from datetime import datetime

# Simple test data
data = {
    "updated": datetime.utcnow().isoformat() + "Z",
    "message": "This is a test update for Widgy Sports Data."
}

with open("sports.json", "w") as f:
    json.dump(data, f, indent=2)

print("sports.json updated")

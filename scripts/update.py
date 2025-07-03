import json
from datetime import datetime

test_data = {
    "status": "success",
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "message": "This is a test file. Data pipeline is working correctly."
}

with open("sports.json", "w") as f:
    json.dump(test_data, f, indent=2)

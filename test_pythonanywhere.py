import os
os.environ["PYTHONANYWHERE_DOMAIN"] = "test"

from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_root():
    response = client.get("/")
    print(response.status_code)
    print(response.json())

if __name__ == "__main__":
    test_root()
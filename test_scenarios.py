import uuid
from cxas_scrapi.core.sessions import Sessions

s = Sessions(app_name="projects/gcp-i-and-d-practitioners/locations/us/apps/maryam-telco-voice-central")

# Test 1: Just text
sid1 = str(uuid.uuid4())
try:
    r = s.run(session_id=sid1, text="Hello")
    print("Test 1 (just text): SUCCESS")
except Exception as e:
    print("Test 1 (just text): FAILED", e)

# Test 2: Just variables
sid2 = str(uuid.uuid4())
try:
    r = s.run(session_id=sid2, variables={"test": "123"})
    print("Test 2 (just variables): SUCCESS")
except Exception as e:
    print("Test 2 (just variables): FAILED", e)

# Test 3: text + variables
sid3 = str(uuid.uuid4())
try:
    r = s.run(session_id=sid3, text="Hello", variables={"test": "123"})
    print("Test 3 (text + variables): SUCCESS")
except Exception as e:
    print("Test 3 (text + variables): FAILED", e)


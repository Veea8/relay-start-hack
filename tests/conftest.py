# Script: conftest.py
# Purpose: Make the backend and the scripts importable in tests and share the schema and the example message
# Author: Andrés Gallardo
# Date: September 2026

import json
import os
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator



# Pin the tolerance share and the split order minutes the expected figures rest on, before anything reads the settings.
# An environment variable wins over a local .env file, so no local setting can change a test result.
os.environ["OVERSHOOT_TOLERANCE_SHARE"] = "0.10"
os.environ["SPLIT_ORDER_WINDOW_MINUTES"] = "120"









#### Step 1: Define the paths ####

# Locate the repository folders from the location of this file
REPOSITORY_FOLDER = Path(__file__).resolve().parent.parent
BACKEND_FOLDER = REPOSITORY_FOLDER / "backend"
SCRIPTS_FOLDER = REPOSITORY_FOLDER / "scripts"



# Point at the published case files, which the tests only ever read
CASE_DATA_FOLDER = REPOSITORY_FOLDER / "data" / "raw" / "2026-09-18_viseca-2026" / "data"
EVENT_SCHEMA_PATH = CASE_DATA_FOLDER / "schemas" / "authorization_event.schema.json"
EXAMPLE_MESSAGE_PATH = CASE_DATA_FOLDER / "scenario_fixtures" / "example_authorization_request.json"



# Check that both files exist before any test runs
assert EVENT_SCHEMA_PATH.is_file(), "The event schema file is missing"
assert EXAMPLE_MESSAGE_PATH.is_file(), "The example message file is missing"









#### Step 2: Make the backend and the scripts importable ####

# Add the backend folder to the import path, so tests can import app.models.events
if str(BACKEND_FOLDER) not in sys.path:
    sys.path.insert(0, str(BACKEND_FOLDER))



# Add the scripts folder to the import path, so tests can import replay
if str(SCRIPTS_FOLDER) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_FOLDER))









#### Step 3: Share the example message and the schema validator ####

# Provide the example message as text, exactly as the file holds it
@pytest.fixture
def example_message_text():
    return EXAMPLE_MESSAGE_PATH.read_text(encoding = "utf-8")



# Provide the example message as a fresh dictionary that a test may change freely
@pytest.fixture
def example_message(example_message_text):
    return json.loads(example_message_text)



# Provide a validator built from the published schema
@pytest.fixture(scope = "session")
def event_schema_validator():
    event_schema = json.loads(EVENT_SCHEMA_PATH.read_text(encoding = "utf-8"))
    Draft202012Validator.check_schema(event_schema)
    return Draft202012Validator(event_schema)

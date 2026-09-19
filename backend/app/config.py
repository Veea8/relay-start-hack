# Script: config.py
# Purpose: Read every setting of the service from the .env file and the environment in one place
# Author: Andrés Gallardo
# Date: September 2026

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict









#### Step 1: Locate the .env file ####

# Build the path from the location of this file, so the working directory never matters
BACKEND_FOLDER = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = BACKEND_FOLDER / ".env"









#### Step 2: Define the settings ####

# Hold every setting of the service, where a real environment variable wins over the .env file
class Settings(BaseSettings):

    # Read the .env file next to the backend code and ignore unrelated entries in it
    model_config = SettingsConfigDict(
        env_file = ENV_FILE_PATH,
        env_file_encoding = "utf-8",
        extra = "ignore",
    )



    # Connect to the authorization service, where the key stays empty for offline work
    leash_base_url: str = "https://saw26api.ashyground-364e1d07.switzerlandnorth.azurecontainerapps.io"
    team_api_key: str = ""



    # Connect to the language model provider, where empty values mean no model is configured
    llm_base_url: str = ""
    llm_model: str = ""
    llm_api_key: str = ""



    # Limit the time for one decision and for the model call inside it, in milliseconds
    engine_budget_ms: int = Field(default = 6000, gt = 0)
    llm_budget_ms: int = Field(default = 2500, gt = 0)



    # Choose what happens when a one-time goal was already bought, and when merchant text tries to instruct the agent
    goal_fulfilled_action: Literal["off", "note", "step_up"] = "note"
    injection_action: Literal["step_up", "decline"] = "step_up"

import os
import sys
import json
import argparse
from pathlib import Path
import requests


def load_env(env_path):
    """Load environment variables from a file."""
    if not os.path.exists(env_path):
        return {}

    env_vars = {}
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip()
    return env_vars


def infer_list_id(title, env_vars):
    """Infer ClickUp List ID based on task title keywords."""
    title_lower = title.lower()

    mapping = {
        "CLICKUP_LIST_MERCHANT_WEB": ["merchant web", "merchant dashboard", "merchant portal"],
        "CLICKUP_LIST_MERCHANT_APP": ["merchant app", "merchant mobile"],
        "CLICKUP_LIST_RIDER_APP": ["rider app", "rider mobile"],
        "CLICKUP_LIST_OPERATION_DASHBOARD": ["ops", "operations", "admin tools"],
        "CLICKUP_LIST_DISPATCHER": ["dispatcher", "dispatch"],
        "CLICKUP_LIST_RECRUITER_VIEW": ["dashboard", "team invites", "calendar integration", "maya bot", "profile", "integrations"],
        "CLICKUP_LIST_JOBS": ["job posting", "job config page", "job creation flow", "job"],
        "CLICKUP_LIST_INTERVIEW": ["interview booking", "scheduling", "interview room"],
        "CLICKUP_LIST_ASSESSMENT": ["assessment creation", "proctoring", "invites", "results"],
        "CLICKUP_LIST_CV_REVIEW": ["cv parsing", "scoring", "matching"],
        "CLICKUP_LIST_TALENT_VIEW": ["apply flow", "talent profile"],
    }

    for env_key, keywords in mapping.items():
        for keyword in keywords:
            if keyword in title_lower:
                return env_vars.get(env_key)

    # Default to DISPATCHER if it's a dispatcher task but doesn't match
    if "dispatcher" in title_lower:
        return env_vars.get("CLICKUP_LIST_DISPATCHER")

    # Default to RECRUITER_VIEW if no match
    return env_vars.get("CLICKUP_LIST_RECRUITER_VIEW")


def map_status(status):
    """Map human status to ClickUp status."""
    status_lower = status.lower()
    mapping = {
        "not started": "to do",
        "currently working on it": "in progress",
        "completed in this session": "in qa",
        "blocked by something external": "blocker",
        "in qa": "in qa",
        "to do": "to do",
        "in progress": "in progress",
        "blocker": "blocker",
    }
    return mapping.get(status_lower, "to do")


def create_clickup_task(title, description, status, env_vars):
    """Create a task in ClickUp."""
    api_token = env_vars.get("CLICKUP_API_TOKEN")
    user_id = env_vars.get("CLICKUP_USER_ID")

    list_id = infer_list_id(title, env_vars)
    if not list_id:
        print(f"Error: Could not determine List ID for task: {title}")
        return False

    url = f"https://api.clickup.com/api/v2/list/{list_id}/task"

    headers = {"Authorization": api_token, "Content-Type": "application/json"}

    payload = {
        "name": title,
        "description": description,
        "status": map_status(status),
        "assignees": [int(user_id)] if user_id else [],
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200 or response.status_code == 201:
        print(f"Successfully created task: {title}")
        return True
    else:
        print(f"Failed to create task: {title}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Log tasks to ClickUp")
    parser.add_argument("--title", help="Task title")
    parser.add_argument("--desc", help="Task description")
    parser.add_argument("--status", default="in qa", help="Task status")
    parser.add_argument("--file", help="Path to a JSON file containing multiple tasks")
    parser.add_argument("--env", default=".claude/clickup.env", help="Path to env file")

    args = parser.parse_args()

    env_vars = load_env(args.env)
    if not env_vars.get("CLICKUP_API_TOKEN"):
        print(f"Error: CLICKUP_API_TOKEN not found in {args.env}")
        sys.exit(1)

    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File {args.file} not found")
            sys.exit(1)

        with open(args.file, "r") as f:
            tasks = json.load(f)
            for task in tasks:
                create_clickup_task(
                    task.get("title"),
                    task.get("description"),
                    task.get("status", "in qa"),
                    env_vars,
                )
    elif args.title and args.desc:
        create_clickup_task(args.title, args.desc, args.status, env_vars)
    else:
        print("Error: Either --title and --desc, or --file must be provided.")
        sys.exit(1)


if __name__ == "__main__":
    main()

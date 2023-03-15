import os
import requests
from github import Github

# Read the GitHub access token from the file
TOKEN_FILE = r"C:\Users\rasmu\OneDrive\Skrivebord\github_token.txt"

with open(TOKEN_FILE, "r") as token_file:
    GITHUB_TOKEN = token_file.read().strip()

# Replace with the GitHub repository you want to get the .py files from
REPO_NAME = "RasmusOtharKirketerp/xolta_public"

gh = Github(GITHUB_TOKEN)
repo = gh.get_repo(REPO_NAME)

output_content = ""

for file in repo.get_contents(""):
    if file.path.endswith(".py"):
        output_content += f"# {'-' * 10} START: {file.path} {'-' * 10}\n"
        output_content += file.decoded_content.decode("utf-8")
        output_content += f"\n# {'-' * 10} END: {file.path} {'-' * 10}\n\n"

# The name of the output file, prefixed with the repo name
repo_name_sanitized = repo.name.replace("/", "_")
OUTPUT_FILE = f"{repo_name_sanitized}_flattened_scripts.py"

with open(OUTPUT_FILE, "w") as output_file:
    output_file.write(output_content)

print(f"Successfully merged .py files from {REPO_NAME} into {OUTPUT_FILE}")

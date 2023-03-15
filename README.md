#GitHub Repository Flattener

This Python script merges all .py files from a specified GitHub repository into a single output file. It can be usefull to feed the ChatGPT or other.
It's useful for quickly combining multiple scripts into a single file for easier distribution or execution.

#Requirements

Python 3.6 or higher
PyGithub library (install with pip install PyGithub)
Usage

#Clone or download this repository to your local machine.
Set the path of your GitHub personal access token file in TOKEN_FILE.
Set the name of the GitHub repository you want to flatten in REPO_NAME.
Run the script with python script_flattener.py.
The output file will be generated in the same directory with the naming format: <repo_name>_flattened_scripts.py.
Configuration

TOKEN_FILE: The path to a file containing your GitHub personal access token. The token should have the repo scope enabled for accessing private repositories. How to create a personal access token: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
REPO_NAME: The full name of the GitHub repository you want to flatten (e.g., "username/repo_name").
Example
TOKEN_FILE = r"C:\Users\rasmu\OneDrive\Skrivebord\github_token.txt"
REPO_NAME = "RasmusOtharKirketerp/xolta_public"

#Output
The script will print a success message to the console after merging the .py files:
Successfully merged .py files from RasmusOtharKirketerp/xolta_public into xolta_public_flattened_scripts.py

The output file will have each script separated by start and end markers, like this:

START: script1.py
...

END: script1.py

START: script2.py
...

END: script2.py

import requests
from requests.auth import HTTPDigestAuth
import subprocess
import time
import threading
import re
import sys
import yaml
import logging
import os
from datetime import datetime

# Function to set up logging for each project with a timestamp
def setup_logging(project_name):
    # Create a logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Get the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define the log file for this project with a timestamp
    log_filename = os.path.join('logs', f'{project_name}_{timestamp}.log')
    
    # Create a logger specifically for this project
    logger = logging.getLogger(project_name)
    logger.setLevel(logging.INFO)
    
    # Create a file handler for logging to the project-specific log file
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    
    # Create a logging format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add the file handler to the logger
    if not logger.handlers:
        logger.addHandler(file_handler)
    
    # Redirect stdout and stderr to the log file
    sys.stdout = open(log_filename, 'a')
    sys.stderr = open(log_filename, 'a')
    
    return logger

# Disclaimer and Warning
def show_disclaimer(agreement, logger=None):
    disclaimer = '''\n
    ****************************************************************************************************
    WARNING: USE THIS SCRIPT AT YOUR OWN RISK
    
    This script is not owned, maintained, or supported by MongoDB, Inc. or any of its employees. 
    By using this script, you acknowledge that any unforeseen consequences or damages resulting 
    from its use are your own responsibility. MongoDB, Inc. and its employees shall not be held 
    liable for any loss, damage, or legal implications that may arise from the use of this script.
    
    IMPORTANT: It is highly recommended that you test this script in a non-risk environment 
    before deploying it in a production environment. Proceed with caution and ensure you fully 
    understand the impact of the actions this script will perform.
    
    ****************************************************************************************************
    '''
    if logger:
        logger.info(disclaimer)
    else:
        print(disclaimer)
        
    if agreement.lower() != "yes":
        if logger:
            logger.info("Exiting script. Please review the disclaimer and ensure you fully understand the risks.")
        else:
            print("Exiting script. Please review the disclaimer and ensure you fully understand the risks.")
        sys.exit(0)

# Headers for the API request
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/vnd.atlas.2024-05-30+json'
}

def get_atlas_api_url(project_id, cluster_name):
    return f'https://cloud.mongodb.com/api/atlas/v2/groups/{project_id}/clusters/{cluster_name}/outageSimulation'

def end_outage_simulation(api_user, api_key, project_id, cluster_name, logger, name):
    url = get_atlas_api_url(project_id, cluster_name)
    
    # Sending the delete request to end the outage simulation
    response = requests.delete(url, headers=headers, auth=HTTPDigestAuth(api_user, api_key))
    
    if response.status_code == 200:
        logger.info(f'\nSuccessfully ended outage simulation for cluster {cluster_name} in project {name}\n')
    else:
        logger.error(f'Failed to end simulation for cluster {cluster_name} in project {name}')
        logger.error(f'Response: {response.text}')

def process_project(project):
    project_id = project['project_id']
    api_user = project['api_user']
    api_key = project['api_key']
    clusters = project['clusters']
    name = project['name']

    # Set up logging for this project
    logger = setup_logging(project['name'])
    
    for cluster in clusters:
        cluster_name = cluster['cluster_name']
        
        logger.info(f"\nEnding outage simulation for cluster '{cluster_name}' in project '{name}'")
        
        # End the outage simulation
        end_outage_simulation(api_user, api_key, project_id, cluster_name, logger, name)

def main(yaml_file):
    with open(yaml_file, 'r') as file:
        config = yaml.safe_load(file)
    
    show_disclaimer(config.get('disclaimer_agreement', 'no'))  # Print disclaimer directly

    threads = []
    for project in config['projects']:
        thread = threading.Thread(target=process_project, args=(project,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python end_outage.py <config_file.yml>")
        sys.exit(1)
    
    yaml_file = sys.argv[1]
    main(yaml_file)

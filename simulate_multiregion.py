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

def get_atlas_api_url(project_id):
    return f'https://cloud.mongodb.com/api/atlas/v2/groups/{project_id}/clusters?pretty=true'

def get_connection_strings_and_regions(api_user, api_key, atlas_api_url, logger):
    try:
        response = requests.get(
            atlas_api_url,
            headers={
                "Accept": "application/vnd.atlas.2024-05-30+json",
                "Content-Type": "application/json"
            },
            auth=HTTPDigestAuth(api_user, api_key)
        )

        if response.status_code == 200:
            clusters = response.json()
            cluster_info = []
            if clusters and 'results' in clusters:
                for cluster in clusters['results']:
                    cluster_name = cluster.get('name', 'N/A')
                    region_configs = cluster.get('replicationSpecs', [{}])[0].get('regionConfigs', [])
                    regions = [(config.get('regionName', 'N/A'), config.get('providerName', 'N/A')) for config in region_configs]
                    connection_string = cluster.get('connectionStrings', {}).get('standard', 'N/A')
                    cluster_info.append((cluster_name, regions, connection_string))

            if cluster_info:
                return cluster_info
            else:
                logger.error("Error: No cluster information found in API response.")
        else:
            logger.error(f"Error: API request failed with status code {response.status_code}")
            logger.error(response.text)
    except Exception as e:
        logger.error(f"Error: An exception occurred while making the API request: {e}")
    return None

def list_primary_secondary_nodes(cluster_name, connection_string, db_username, db_password, project_id, logger, name):
    try:
        logger.info(f"Listing primary and secondary nodes for cluster: {cluster_name} in project {name}")
        mongosh_command = [
            "mongosh", connection_string,
            "--username", db_username,
            "--password", db_password,
            "--eval", "rs.status().members.forEach(member => print(`${member.name} - ${member.stateStr}`))"
        ]
        result = subprocess.run(mongosh_command, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("\nPrimary and Secondary nodes:\n")
            logger.info(result.stdout)
        else:
            logger.error(f"Error: mongosh command failed with return code {result.returncode}")
            logger.error(result.stderr)
    except Exception as e:
        logger.error(f"Error: An exception occurred while running mongosh: {e}")

def start_outage_simulation(api_user, api_key, project_id, cluster_name, cloud_provider, region_name, logger, name):
    url = f'https://cloud.mongodb.com/api/atlas/v2/groups/{project_id}/clusters/{cluster_name}/outageSimulation'
    payload = {
        "outageFilters": [
            {
                "cloudProvider": cloud_provider,
                "regionName": region_name,
                "type": "REGION"
            }
        ]
    }
    
    response = requests.post(url, headers=headers, auth=HTTPDigestAuth(api_user, api_key), json=payload)
    
    if response.status_code == 200:
        logger.info(f'\nSuccessfully started regional outage simulation for cluster {cluster_name} in project {name}\n')
    else:
        logger.error(f'Failed to start simulation for cluster {cluster_name} in project {project_id}')
        logger.error(f'Response: {response.text}')

def check_simulation_status(api_user, api_key, project_id, cluster_name, connection_string, db_username, db_password, logger, name):
    not_found_count = 0

    while True:
        try:
            url = f'https://cloud.mongodb.com/api/atlas/v2/groups/{project_id}/clusters/{cluster_name}/outageSimulation'
            response = requests.get(url, headers=headers, auth=HTTPDigestAuth(api_user, api_key))

            if response.status_code == 200:
                if not response.json():
                    logger.info(f'\nSimulation for cluster {cluster_name} in project {name} is complete (empty response).\n')
                    break
                else:
                    simulation_state = response.json().get('state', 'UNKNOWN')
                    logger.info(f'\nSimulation state for cluster {cluster_name} in project {name} : {simulation_state}\n')
                    
                    if simulation_state == 'COMPLETE':
                        break
                    time.sleep(10)
            elif response.status_code == 404:
                not_found_count += 1
                logger.info(f'COMPLETE State received for cluster {cluster_name}. Attempt {not_found_count}/5.')
                if not_found_count >= 5:
                    logger.info(f'Simulation for cluster {cluster_name} in project {name} is considered complete after 5 consecutive COMPLETE state.')
                    break
                else:
                    time.sleep(10)
            else:
                logger.error(f'Unexpected status code {response.status_code} for cluster {cluster_name} in project {name}')
                break

        except requests.exceptions.RequestException as e:
            logger.error(f'Error checking simulation status for cluster {cluster_name} in project {project_id}: {e}')
            break

    list_primary_secondary_nodes(cluster_name, connection_string, db_username, db_password, project_id, logger)

def start_outage_for_project(api_user, api_key, project_id, clusters, db_username, db_password, logger, name):
    cluster_info = get_connection_strings_and_regions(api_user, api_key, get_atlas_api_url(project_id), logger)
    
    for cluster in clusters:
        logger.info(f"\nProcessing cluster data: {cluster}")  # Debugging log
        
        cluster_name = cluster.get('cluster_name')
        region_name = cluster.get('region_name')
        cloud_provider = cluster.get('cloud_provider')

        if cluster_name is None or region_name is None or cloud_provider is None:
            logger.error("Error: 'cluster_name', 'region_name', or 'cloud_provider' missing in the YAML file for one of the clusters.")
            continue

        logger.info(f"\nStarting outage simulation for cluster '{cluster_name}'")

        # Verify that the region is available for this cluster
        connection_string = None
        valid_region = False
        for info in cluster_info:
            if info[0] == cluster_name:
                connection_string = info[2]
                for region, provider in info[1]:
                    if region == region_name and provider == cloud_provider:
                        valid_region = True
                        break
                break
        
        if not connection_string:
            logger.error(f"Error: Could not find connection string for cluster '{cluster_name}'")
            continue
        
        if not valid_region:
            logger.error(f"Error: Specified region '{region_name}' with cloud provider '{cloud_provider}' is not valid for cluster '{cluster_name}'")
            continue

        list_primary_secondary_nodes(cluster_name, connection_string, db_username, db_password, project_id, logger, name)
        start_outage_simulation(api_user, api_key, project_id, cluster_name, cloud_provider, region_name, logger, name)
        time.sleep(1)

    logger.info("\nWaiting for 2 minutes before checking the simulation status...\n")
    time.sleep(120)

    threads = []
    for cluster in clusters:
        cluster_name = cluster['cluster_name']
        connection_string = None
        for info in cluster_info:
            if info[0] == cluster_name:
                connection_string = info[2]
                break
        
        if connection_string:
            thread = threading.Thread(target=check_simulation_status, args=(api_user, api_key, project_id, cluster_name, connection_string, db_username, db_password, logger, name))
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()

def process_project(project):
    project_id = project['project_id']
    api_user = project['api_user']
    api_key = project['api_key']
    db_username = project['db_username']
    db_password = project['db_password']
    clusters = project['clusters']
    name = project['name']

    # Set up logging for this project
    logger = setup_logging(project['name'])
    
    start_outage_for_project(api_user, api_key, project_id, clusters, db_username, db_password, logger, name)

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
        print("Usage: python simulate_multiregion.py <config_file.yml>")
        sys.exit(1)
    
    yaml_file = sys.argv[1]
    main(yaml_file)

# atlas-cluster-outage-simulation

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

These are the scripts that can be used to create and end the outage simulation for region failover.

Run the simulate_multiregion.py as below:

- To run the script in the background, use:
  
```python
nohup python3 simulate_multiregion.py projects_config_template.yml &

```

The script will now process each project in parallel, using the specified cluster name, region name, and cloud provider from the YAML configuration.

All logs will be saved in the logs directory, and you can monitor the progress by checking this file.
- Each project will have it's own log file with the timestamp when the simulation was triggered, therefore making it easier for audit purpose.

To end the outage run the below command:

```python
python3 end_outage.py projects_config_template.yml

```

The end script will ensure tha the outage ends on all the clusters, and will log the execution.

**The disclaimer statement is auto-accepted as per the value `YES` in the yml file. Please read the disclaimer and use the script at your own discretion.**

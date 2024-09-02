# atlas-cluster-outage-simulation
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

The end script will ensure tha the outage ends on all the clusters, and will log in the same log file to ensure continuity of the log.

**The disclaimer statement is auto-accepted as per the value `YES` in the yml file. Please read the disclaimer and use the script at your own discretion.**

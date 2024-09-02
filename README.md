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

These are the scripts that can be used to create and end the outage simulation for region failover. This script matches the list of region by getting the cluster details and if the region_name in the yml file matches one of the regions, it will bring DOWN that mentioned region. Also, this will print the list of nodes with their replState every 5 mins during the simulation.

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

## Multi-Threading:

There can be some issues if you have more projects than the number of threads available on your system. The primary concerns include:

### 1. **Thread Contention**:
   - **Context Switching Overhead**: If you have too many threads, the operating system spends a significant amount of time switching between threads (context switching), which can lead to inefficiencies and slow down the overall execution.
   - **Resource Contention**: Threads share system resources like CPU, memory, and I/O. If too many threads are competing for these resources, it can lead to contention, where threads are waiting for access to resources, further slowing down the execution.

### 2. **System Limits**:
   - **Thread Limits**: Some systems have a limit on the number of threads that can be created by a process. If your script attempts to create more threads than the system allows, you may encounter errors or unexpected behavior.
   - **Memory Usage**: Each thread consumes a certain amount of memory. If you create too many threads, you could exhaust the system's memory, leading to crashes or the system becoming unresponsive.

### 3. **Inefficient CPU Usage**:
   - **Overloading the CPU**: If the number of threads exceeds the number of CPU cores, many threads will be idle while waiting for CPU time. This can lead to inefficiencies, as the system spends more time managing threads than doing actual work.

### Explanation on how this has been handled:

1. **`ThreadPoolExecutor`**:
   - `concurrent.futures.ThreadPoolExecutor` is used to manage a pool of worker threads. The `max_workers` parameter controls the maximum number of threads that can be active simultaneously.
   
2. **Adjusting `max_workers`**:
   - The `max_workers` value is set based on the number of CPU cores (`os.cpu_count()`) plus a buffer (e.g., `+4`) for handling I/O-bound tasks.

3. **Submitting Tasks**:
   - Each project is submitted to the thread pool for processing using `executor.submit`. The thread pool manages how these tasks are executed.

4. **Handling Results**:
   - `concurrent.futures.as_completed(futures)` is used to handle the results of the tasks. This ensures that any exceptions raised during execution are handled properly.

### Benefits:

- **Controlled Concurrency**: The thread pool controls the number of active threads, preventing resource exhaustion and contention.
- **Scalability**: The script can handle a large number of projects efficiently by queuing them up and processing them as threads become available.

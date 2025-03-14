# Context and Goal

This algorithm is designed to **optimize a sequential production line** consisting of an undefined number of machines and 
different product types. The main objective is to determine the **most efficient production sequence** that **minimizes production line downtime**.

To achieve this, the algorithm integrates:
- A production simulation based on **survival functions** and **degradation models**
- An **optimization** approach using **Simulated Annealing**

Each machine has an associated **survival probability function**, which determines 
the probability of a machine continuing to operate without failure or requiring maintenance based on the number of cycles it has completed. This probability is used to **schedule maintenance 
strategically**, preventing breakdowns.

# Table of Contents

1. Algorithm Description
2. Algorithm Flow and Logic
3. Repository Organization


# 1. Algorithm Description and Parameters

##  1.1. Some Assumptions/Considerations 

- The production and production line follow a **sequential order**.
- A **product** moves to the next machine only after completing all operations on the previous one.
- The **duration of maintenance** is the same for all machines, and is measured/defined in cycles.
- A **timeslot** refers to the duration of a single machine cycle, and this duration is the same for all machines.
- The machines can have **different survival** functions.
- If one **machine** is under **maintenance**, all others **must pause production**.
- More than one machine can be **under maintenance at the same time**.


## 1.2. Simulation Parameters

  ### 1.2.1. Cycle Mapping

  Each product type requires a fixed number of operating cycles on specific machines. This relationship is defined as the 
  "**Required Production Cycles per Product per Machine**" mapping.

  For example, consider a product `A0` that needs to pass through two machines (`m1` and `m2`) with the following production
  requirements:
```
{
    "m1": {"A0": 5},
    "m2": {"A0": 7}
}
```

For a **real-world analogy**, imagine `m1` and `m2` as welding machines and `A0` as a car door, where `m1` must perform 5 welds
on the car door, and `m2` performs 7 additional welds before the product is complete. So this mapping ensure that the 
production can be scheduled considering for different product types their machine requirements.

### 1.2.2. Minimum and Maximum Survival Probability for Maintenance

It is considered that **machines require maintenance at specific survival probability thresholds**. For example, when the 
survival probability of a machine falls within the defined range (for instance, between 0.2 and 0.3), the machine must undergo maintenance.
This ensures that machines are **repaired before the risk of failure becomes too high**, while **avoiding unnecessary early maintenance**.
Example:

```
    s_maintenance_min = 0.2
    s_maintenance_max = 0.3
```

### 1.2.3. Initial Machine Cycles

Each machine starts the simulation with a predefined **cycle count** that represents the **number of production cycles 
completed since the last maintenance**. It must be clear that a machine that has just undergone maintenance starts at 0 cycles. 
With each production cycle, the count increases by 1.

For example, if a machine has an initial cycle count of 1400, it means that before the start of the simulation, the 
machine had already operated for 1400 production cycles. The cycle count is used to monitor the machine's state over the
production, helping to determine when maintenance is required. Example:

```
    initial_cycles = {
                        'm1': 7900,
                        'm2': 1400,
                        'm3': 3581
    }
```

### 1.2.4. Maintenance Duration

This defines how long a machine remains unavailable while undergoing maintenance, measured in cycles.

```
    maintenance_duration = 5 
```
## 1.3. Production Requirements

Once the simulation parameters are set, the production requirements must be defined:

### 1.3.1. Available Machines
Specifies which machines are operational and available for production. The machines are labeled `m1`, `m2`, and so on.
Example:

```
  operating_machines_list = ['m1','m2, m3']
```

### 1.3.2. Product Types and Quantities 
Defines how many units of each product type need to be produced during the simulation. The product types follow the format `A0`, `A1`, etc. 
Example:

```
production_requirements_dict = {  
        "A0": 30,
        "A1": 30,
        "A2": 40,
        "A3": 40
    }
```

# 2. Algorithm Flow and Logic

In this section the production simulation and optimization will be described.

Once all the required parameters are defined, the algorithm begins by **generating a random initial production sequence**,
based on the production requirements. For example, given the following requirements:

```
{  
    "A0": 3,
    "A1": 1,
    "A2": 1,
    "A3": 0.
}
```

The initial sequence may look like this: `['A0', 'A2', 'A0', 'A1', 'A0']`.

This sequence is then passed to the optimization algorithm (`simulated_annealing`). In every iteration, **the sequence is evaluated**
based on the production line **downtime** duration returned by the production simulation (`production_simulation`). Based on that result
, and following the logic of the **Simulated Annealing**, the **sequence is modified and evaluated again** until the algorithm finds the **optimal
sequence that minimizes the downtime**, or reaches the stagnation or maximum iterations value.

## 2.1. Production Simulation

The `production_simulation` function **simulates the production process**, taking into account the need for maintenance, the required products 
and their production sequence, and aims to minimize downtime. This function attempts, if maintenance is needed for any machine, to 
synchronize it for all operating ones, reducing its impact on the production line. 

> **Maintenance Scheduling Example** <br>
For example, assuming a maintenance period of 5 cycles, if it is calculated that, for a given production sequence,
`m1` will be within the defined survival probability thresholds (i.e. requires maintenance) from timeslots `t56` to `t150`, and `m2` will be within those 
thresholds from timeslots `t80` to `t186`, the algorithm will schedule the maintenance, for example, from timeslots `t80` to `t85`.

> **Scheduling Framework** <br>
The production and maintenance scheduling is performed based on a scheduling table (`schedule`) that is defined before the simulation starts.
The `schedule` is structured as follows:  <br>
>  - **Rows**: Represent available machines. <br>
>  - **Columns**: Represent timeslots in the format tx, where x=0 marks the start of the simulation. <br>
>      - Possible states for each timeslot: <br>
>         - "_Free_" <br>
>         - "_Producing_" <br>
>         - "_Maintenance_" <br>
>         - "_Unavailable_" (when a machine can't produce because another machine is under maintenance)

> **Machine Operating Tracking** <br>
In addition to the `schedule` table, the algorithm keeps a nested dictionary, `machine_operation_information`, 
that records machine activity over time:
```
    -> Machine 'mx'
       -> Timeslot 'ty'
          - Product: ID of the product being processed (e.g., "A0_4" for the 4th A0 unit)
          - Cycle: Current machine cycle count
          - State: "Producing" / "Free" / "Maintenance" / "Unavailable"
    
    Example:
        m1:
           t9  -> cycle_number : 100, production_flag  : "Producing", product_label : "A3_4"
           t10 -> cycle_number : 0,   production_flag  : "Free",      product_label : None
```

These structures are **dynamically updated** throughout `production_simulation` to keep machine states and production **tracking 
in sync**. When a product begins processing, the corresponding machine's state, cycle count, and other relevant details are 
updated in the respective structure. This ensures an **accurate representation of machine availability** and enables the 
simulation to **reflect the machines' state progression** over the entire production sequence simulation.

The steps of the `production_simulation` function are described below.

### 2.1. a.	Process Production Sequence
-   The production sequence is processed by the `divide_production_sequence` function. That function begins by calculating 
the number of machine cycles required for each timeslot, for each machine, using the `calculate_required_cycle_for_production_sequence` function. Output example: 
```
    production_sequence = [A0, A3, A4, A1, A0]
    m1: [0, 5, 6, 7, 7]

        - m1 will be used 0 cycles for the 1st product in the sequence
        - will be used 5 additional cycles for the 2nd product
        - 1 more cycle for the 3rd product (5+1)
        - ...
```
-	If the sequence requires more cycles than a machine can operate before requiring maintenance, the sequence is split into two parts. 
For instance, considering the example above, if `m1` is likely to required maintenance after 6 operation cycles, the production sequence will have be 
split into `production_sequence_1 = [A0, A3, A4]` and `production_sequence_2 = [A1, A0]`. 

-	The split occurs at the last timeslot/product where all machines can operate without reaching the survival probability threshold for maintenance.

### 2.1. a.1.	Handle Maintenance
-	If a machine requires maintenance, it is marked in the `schedule` and cannot operate during the maintenance period.
-	Since production is sequential, if one machine is under maintenance, all machines must stop until maintenance is completed.
-	After maintenance, **the machine's cycle count is reset to 0**.

### 2.1. b.	Sequential Production Execution
-	The first half of the divided sequence (or the whole sequence, if the division was not needed) is scheduled, ensuring 
each product follows the required operation cycles and machine dependencies.
-	After processing the first half, the second half is evaluated:
    -	If the remaining sequence exceeds the machine’s maintenance limit, it is divided again.
    -	This process repeats until all products are fully produced.
  
### 2.1. c.	Output Results
-   The final production timeline is determined by identifying the first timeslot where all machines are "Free".
-	At the end of the production simulation, the **total downtime** is calculated and returned.



## 2.2. Optimization with Simulated Annealing

The **Simulated Annealing**  algorithm is applied **iteratively** to improve the production sequence, reducing downtime and 
minimizing maintenance intervals. As was described previously, the optimization algorithm follows these steps:

1. Generate an initial random sequence.
2. Evaluate total downtime from the `production_simulation` function.
3. Modify the sequence and re-evaluate the downtime.
4. Accept the new sequence based on Simulated Annealing criteria.
5. Repeat until:
   - The optimal sequence is found (minimizing downtime), or
   - The maximum iterations/stagnation limit is reached.

After finding the optimal sequence, a simulation log is saved, following the format of the example below:

````
*****************************************************
Started simulation at 2025-02-10 15:49:13.778883
*****************************************************
 
SIMULATION PARAMETERS:
  - product_machine_cycles_mapping_dict: {'m1': {'A0': 50, 'A1': 2, 'A2': 0, 'A3': 0}, 'm2': {'A0': 0, 'A1': 2, 'A2': 50, 'A3': 0},
 'm3': {'A0': 0, 'A1': 2, 'A2': 0, 'A3': 50}}
  - maintenance_duration: 5
  - cycle_duration: 1
  - initial_cycles: {'m1': 7900, 'm2': 7800, 'm3': 7800}
  - s_maintenance_min: 0.1985
  - s_maintenance_max: 0.2
 
REQUIRED PRODUCTION INFORMATION:
  - production_requirements_dict: {'A0': 30, 'A1': 30, 'A2': 40, 'A3': 40}
  - operating_machines_list: ['m1', 'm2', 'm3']
 
OPTIMIZATION AND SIMULATION DURATION: 4.08 minutes
 
SIMULATION RESULTS
Optimal Production Sequence: ['A1', 'A0', 'A3', 'A1', 'A3', 'A2', 'A0', 'A3', 'A1', 'A3', 'A2', 'A2', 
'A1', 'A1', 'A0', 'A3', 'A0', 'A3', 'A0', 'A2', 'A0', 'A1', 'A2', 'A3', 'A2', 'A3', 'A0', 'A2', 'A2',
'A1', 'A0', 'A0', 'A2', 'A2', 'A3', 'A1', 'A0', 'A3', 'A3', 'A2', 'A0', 'A1', 'A3', 'A2', 'A3', 'A3',
'A2', 'A2', 'A0', 'A2', 'A0', 'A2', 'A3', 'A3', 'A3', 'A0', 'A1', 'A0', 'A3', 'A3', 'A1', 'A3', 'A1',
'A2', 'A0', 'A2', 'A0', 'A0', 'A3', 'A3', 'A1', 'A1', 'A3', 'A3', 'A2', 'A3', 'A1', 'A1', 'A3', 'A2', 
'A1', 'A1', 'A3', 'A3', 'A3', 'A3', 'A1', 'A2', 'A1', 'A1', 'A0', 'A2', 'A1', 'A2', 'A1', 'A2', 'A2', 
'A3', 'A1', 'A0', 'A3', 'A3', 'A1', 'A3', 'A3', 'A2', 'A1', 'A3', 'A2', 'A3', 'A1', 'A2', 'A2', 'A0', 
 'A0', 'A0', 'A2', 'A2', 'A0', 'A1', 'A2', 'A0', 'A0', 'A3', 'A0', 'A3', 'A2', 'A1', 'A1', 'A2', 'A0', 
 'A3', 'A0', 'A0', 'A2', 'A2', 'A2', 'A2', 'A2', 'A2']
 
SIMULATION RESULTS - PRODUCTION
  - Production duration (in cycles): 2222
  - Cycles used by machine m1: 1560
  - Cycles used by machine m2: 2060
  - Cycles used by machine m3: 2060
  - Total of produced products: 140
      - A0: 30
      - A1: 30
      - A2: 40
      - A3: 40
 
SIMULATION RESULTS - MAINTENANCE
  - Total production downtime (in cycles): 5
  - Number of times machine m1 was under maintenance: 1
      - from t6 to t10
  - Number of times machine m2 was under maintenance: 1
      - from t6 to t10
  - Number of times machine m3 was under maintenance: 1
      - from t6 to t10
````

The `schedule` and `machine_operation_information` are also saved as Excel files. 

# 3. **Repository Organization**

The repository is organized as follows:

- **`/data`**
  - **`/base_survival_function`**: Stores the .csv files containing survival function data for the machines.
  - **`/logs`**: Stores log files generated during the simulation.
  - **`/plots`**: Stores plots for visualizing production and maintenance statistics.
  - **Schedule and machine operation information files:** The output .xlsx files for the schedule and machine operation details are stored here.

- **`main`**: Defines the simulation parameters and production requirements; serves as the entry point of the program.
- **`file_operations`**:  Handles reading and writing data, including exporting schedule and machine operation information as Excel files.
- **`optimization_algorithm`**: Implements the simulated annealing algorithm for optimizing the production sequence.
- **`plot_print_operations`**: Manages data visualization, including survival probability plots over cycles for all operating machines, as well as logging and printing simulation statistics.
- **`schedule_operations`**: Defines functions for scheduling production and maintenance activities.
- **`simulation_operations`**: Contains the production simulation logic, including machine state tracking and scheduling updates.
- **`survival_function_operations`**: Manages survival probability calculations to determine maintenance needs.
- **`user_input_operations`**: Handles user interactions via the terminal, including parameter input and configuration settings.


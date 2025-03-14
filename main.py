import random
import logging
import datetime
import time

from survival_function_operations import starting_survival_function_data
from simulation_operations import production_simulation
from optimization_algorithm import simulated_annealing
from user_input_operations import user_input_simulation_interface
from plot_print_operations import format_duration

log_file_path = r'data/logs/production_simulation_log.log'
logger = logging.getLogger()

user_input_active = 0 # if the flag is set to 1, the simulation parameters can be edited directly in the terminal
                      # and the production requirements must be provided by the user

def main():

    logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(message)s' )
    current_date_time = datetime.datetime.now()

    logger.info('*****************************************************')
    logger.info(f'Started simulation at {current_date_time}')
    logger.info('*****************************************************')
    logger.info(' ')

    # simulation parameters:

    maintenance_duration = 5  # duration of the maintenance time (in cycles)
    cycle_duration = 1  # duration of each cycle

    s_maintenance_min = 0.1985  # threshold values of the survival probability at which machine maintenance is recommended
    s_maintenance_max = 0.2

    product_machine_cycles_mapping_dict = { # mapping between cycles required for each product for each machine

        "m1": {"A0": 50, "A1": 2, "A2": 0, "A3": 0},
        "m2": {"A0": 0, "A1": 2, "A2": 50, "A3": 0},
        "m3": {"A0": 0, "A1": 2, "A2": 0, "A3": 50}
    }

    initial_cycles = { # starting cycles for each machine
        'm1': 7100,
        'm2': 5000,
        'm3': 7100
    }

    # production requirements:

    operating_machines_list = [f"m{i}" for i in range(1, 4)]  # operating machines

    production_requirements_dict = {  # the type and number of products to produce
        "A0": 180,
        "A1": 180,
        "A2": 200,
        "A3": 180
    }

    survival_dict = {}  # aux dict - to store the starting survival function for all the machines

    if user_input_active == 1:
        user_input_simulation_interface(product_machine_cycles_mapping_dict, maintenance_duration, cycle_duration, initial_cycles, s_maintenance_min, s_maintenance_max)

    logger.info(f'SIMULATION PARAMETERS:')
    logger.info(f'  - product_machine_cycles_mapping_dict: {product_machine_cycles_mapping_dict}')
    logger.info(f'  - maintenance_duration: {maintenance_duration}')
    logger.info(f'  - cycle_duration: {cycle_duration}')
    logger.info(f'  - initial_cycles: {initial_cycles}')
    logger.info(f'  - s_maintenance_min: {s_maintenance_min}')
    logger.info(f'  - s_maintenance_max: {s_maintenance_max}')
    logger.info(' ')

    logger.info(f'REQUIRED PRODUCTION INFORMATION:')
    logger.info(f'  - production_requirements_dict: {production_requirements_dict}')
    logger.info(f'  - operating_machines_list: {operating_machines_list}')
    logger.info(' ')

    print('\nRequested production:', production_requirements_dict)

    print('\n-------------------------------------------------')
    print('     SIMULATION')
    print('-------------------------------------------------')

    for m in operating_machines_list: starting_survival_function_data(m, survival_dict)

    #  turn the production requirements into an initial random production sequence
    initial_sequence = [product for product, count in production_requirements_dict.items() for _ in range(count)]
    random.shuffle(initial_sequence)

    start_time_simulation = time.time()
    optimized_sequence, optimized_downtime, best_maintenance_intervals = simulated_annealing(initial_sequence,operating_machines_list,
                                                                                             product_machine_cycles_mapping_dict,
                                                                                             maintenance_duration,s_maintenance_min,
                                                                                             s_maintenance_max,
                                                                                             survival_dict,initial_cycles,
                                                                                             production_requirements_dict)

    simulation_duration = round(time.time() - start_time_simulation, 2)

    print('\n   -------------------------------------------------')
    print('          RESULTS')
    print('   -------------------------------------------------')

    print('\n   Optimization + Simulation Duration', format_duration(simulation_duration))
    logger.info(f'OPTIMIZATION AND SIMULATION DURATION: {format_duration(simulation_duration)}')
    logger.info(' ')

    print("\n   Optimal Production Sequence:", optimized_sequence)
    print("   Suggested Intervals to Schedule Maintenance to Reduce Downtime:", best_maintenance_intervals)
    print("   Total Downtime:", optimized_downtime*cycle_duration, 'cycles')

    _,_ =  production_simulation(production_requirements_dict, optimized_sequence, operating_machines_list,
                          initial_cycles, product_machine_cycles_mapping_dict, maintenance_duration,
                          s_maintenance_min, s_maintenance_max, survival_dict, logger, optimized_sequence)

    print(f"Logged simulation statistics in {log_file_path}.")


if __name__ == '__main__':
    main()

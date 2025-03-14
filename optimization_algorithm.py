import random
import math

from simulation_operations import production_simulation

def simulated_annealing(initial_sequence, operating_machines_list, product_machine_cycles_mapping_dict, maintenance_duration, s_maintenance_min, s_maintenance_max, survival_dict, initial_cycles, production_requirements_dict):

    print('\nOptimization with Simulated Annealing...')

    # SA parameters
    current_sequence = initial_sequence
    current_temp = 1000
    min_temp = 0.1
    alpha = 0.95  # cooling factor
    max_iterations = 5000

    tested_sequences = set() # to store already tested sequences
    tested_sequences.add(tuple(current_sequence))

    current_best_maintenance_intervals, current_downtime = production_simulation(production_requirements_dict, current_sequence, operating_machines_list,
                                                                                 initial_cycles, product_machine_cycles_mapping_dict, maintenance_duration,
                                                                                 s_maintenance_min, s_maintenance_max, survival_dict, logger=None, optimized_sequence=None)

    stagnation_count = 0 # counter for stagnation
    max_stagnation = 100  # max iterations without finding a new sequence

    for iteration in range(max_iterations):

        if current_temp < min_temp:
            break

        # generate a neighboring solution by swapping 4 products in the sequence
        neighbor_sequence = current_sequence[:]
        i, j, w, k = random.sample(range(len(current_sequence)), 4)
        neighbor_sequence[i], neighbor_sequence[j], neighbor_sequence[w], neighbor_sequence[k] = neighbor_sequence[k], neighbor_sequence[w], neighbor_sequence[i], neighbor_sequence[j]

        neighbor_tuple = tuple(neighbor_sequence)

        if neighbor_tuple in tested_sequences:
            continue # skip this neighbor if it has already been tested

        # print(f'\nSequence {neighbor_sequence}')

        tested_sequences.add(neighbor_tuple)

        # print(' Simulating...')
        neighbor_best_maintenance_intervals, neighbor_downtime = production_simulation(production_requirements_dict, neighbor_sequence, operating_machines_list,
                                                                                       initial_cycles, product_machine_cycles_mapping_dict, maintenance_duration,
                                                                                       s_maintenance_min, s_maintenance_max, survival_dict, logger=None, optimized_sequence=None)

        # print(f'    Downtime: {neighbor_downtime}, Maintenance Intervals: {neighbor_best_maintenance_intervals}')

        if neighbor_downtime < current_downtime:
            current_sequence = neighbor_sequence
            current_downtime = neighbor_downtime
            current_best_maintenance_intervals = neighbor_best_maintenance_intervals
            stagnation_count = 0  # reset stagnation count since a better sequence was found

        else:
            delta = current_downtime - neighbor_downtime
            acceptance_probability = math.exp(delta / current_temp)

            if random.random() < acceptance_probability:
                current_sequence = neighbor_sequence
                current_downtime = neighbor_downtime
                stagnation_count = 0

        if neighbor_tuple not in tested_sequences:
            stagnation_count = 0

        else: # if this sequence has already been tested, increase the stagnation
            stagnation_count += 1

        if stagnation_count >= max_stagnation:
            break

        current_temp *= alpha

    return current_sequence, current_downtime, current_best_maintenance_intervals
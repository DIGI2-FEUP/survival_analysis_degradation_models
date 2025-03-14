from survival_function_operations import get_survival_cycles

from file_operations import save_schedule_and_machine_operation_information_excel_files

from schedule_operations import schedule_setup
from schedule_operations import update_schedule_for_product
from schedule_operations import update_schedule_for_maintenance

from plot_print_operations import plot_survival_prob_over_cycles
from plot_print_operations import print_stats_maintenance
from plot_print_operations import print_stats_production

def calculate_downtime(maintenance_intervals):

    """
            Calculates the production downtime, in cycles, given the maintenance intervals.
    """

    intervals = [(maintenance_start_time, maintenance_end_time) for _, (maintenance_start_time, maintenance_end_time) in maintenance_intervals]

    intervals.sort() # sort by start time
    merged_intervals = []

    for start, end in intervals:

        if not merged_intervals or merged_intervals[-1][1] < start - 1:
            merged_intervals.append((start, end))

        else:
            merged_intervals[-1] = (merged_intervals[-1][0], max(merged_intervals[-1][1], end))

    total_downtime = sum(end - start + 1 for start, end in merged_intervals)

    return total_downtime


def calculate_required_cycle_for_production_sequence(product_machine_cycles_mapping_dict, production_sequence, operating_machines_list):

    """
        Calculates the cumulative cycles for each machine based on a given production sequence.

        Example output -> m1: [0, 5, 6, 7, 7]
                            - m1 was used 0 cycles for the 1st product in the sequence
                            - was used 5 additional cycles for the 2nd product
                            - 1 more cycle for the 3rd product (5+1)
                            - ...
    """

    required_cycles_for_production_sequence = {
        machine: [] for machine in operating_machines_list
    }

    accumulated_cycles = {machine: 0 for machine in operating_machines_list}

    for product in production_sequence:

        for machine in operating_machines_list:

            cycles = product_machine_cycles_mapping_dict[machine].get(product, 0)
            accumulated_cycles[machine] += cycles
            required_cycles_for_production_sequence[machine].append(accumulated_cycles[machine])

    return required_cycles_for_production_sequence

def calculate_remaining_cycles_until_recommended_maintenance(machine_cycle_numbers, s_maintenance_max, s_maintenance_min, operating_machines_list, survival_dict):

    """
        Calculates how many cycles each machine has to complete until it's recommended maintenance interval.
    """

    remaining_cycles_until_start_of_recommended_maintenance = {
        machine: [] for machine in operating_machines_list
    }

    remaining_cycles_until_end_of_recommended_maintenance = {
        machine: [] for machine in operating_machines_list
    }

    for machine in operating_machines_list:

        current_cycle = machine_cycle_numbers[machine]

        cycle_for_start_of_recommended_maintenance =  get_survival_cycles(machine, s_maintenance_max, survival_dict)
        remaining_cycles_until_start_of_recommended_maintenance[machine].append(cycle_for_start_of_recommended_maintenance - current_cycle)

        cycle_for_end_of_recommended_maintenance = get_survival_cycles(machine, s_maintenance_min, survival_dict)
        remaining_cycles_until_end_of_recommended_maintenance[machine].append(cycle_for_end_of_recommended_maintenance - current_cycle)

    return remaining_cycles_until_start_of_recommended_maintenance, remaining_cycles_until_end_of_recommended_maintenance


def divide_production_sequence(product_machine_cycles_mapping_dict, production_sequence, operating_machines_list, machine_cycle_numbers,
                               s_maintenance_max, s_maintenance_min, survival_dict):

    """
        Divides the production sequence into two parts based on machine maintenance intervals.
        The separation point is determined by the machine with the lowest remaining cycles before maintenance.
    """

    required_cycles_for_production_sequence = calculate_required_cycle_for_production_sequence(product_machine_cycles_mapping_dict, production_sequence, operating_machines_list)
    remaining_cycles_until_start_of_recommended_maintenance, remaining_cycles_until_end_of_recommended_maintenance = calculate_remaining_cycles_until_recommended_maintenance(machine_cycle_numbers, s_maintenance_max, s_maintenance_min, operating_machines_list,survival_dict)

    machines_separation_position = {
        machine: [] for machine in operating_machines_list
    }

    for machine in remaining_cycles_until_start_of_recommended_maintenance.keys():

        machine_separation_position = 0

        for acumulated_cycles in required_cycles_for_production_sequence[machine]:

            if acumulated_cycles < remaining_cycles_until_start_of_recommended_maintenance[machine][0]:
                machine_separation_position += 1 # increment the separation position until the accumulated cycles are greater than the machine's remaining cycles before maintenance

            else:
                machines_separation_position[machine].append(machine_separation_position)
                break

    if all(len(positions) == 0 for positions in machines_separation_position.values()): #if there is no need to divide the sequence <=> the machines can produce the sequence without any maintenance intervals
        return None, production_sequence, None


    valid_machines = [(k, v[0]) for k, v in machines_separation_position.items() if v] # only non-empty lists for separation positions

    if not valid_machines:
        return None, production_sequence, None


    machine_for_separation_position, min_separation_position = min(valid_machines, key=lambda item: item[1]) # find the smallest separation position among machines to ensure that no machine operates past its maintenance interval
    all_other_separation_positions = [position for _, position in valid_machines if position != min_separation_position]

    if all(other_position > min_separation_position + 100 for other_position in all_other_separation_positions):
        valid_machines = [(machine_for_separation_position, min_separation_position)]


    if min_separation_position == 0: # the machine needs immediate maintenance before producing

        # print('\n-------------------------------------------------------------------')
        # print('\nPRODUCTION WARNING')
        # print(f'   Machine {machine_for_separation_position} needs immediate maintenance before producing.')

        return machine_for_separation_position, None, None

    if len(valid_machines) == 1: # if only one machine needs maintenance

        first_production_sequence = production_sequence[:min_separation_position]
        second_production_sequence = production_sequence[min_separation_position:]

        return machine_for_separation_position, first_production_sequence, second_production_sequence

    elif len(valid_machines) > 1: # if multiple machines need maintenance, check for any overlapping intervals

        # print('\n-------------------------------------------------------------------')
        # print('\nCHECKING FOR POSSIBLE SIMULTANEOUS MAINTENANCE...')

        overlapping_intervals = check_for_maintenance_overlap(remaining_cycles_until_start_of_recommended_maintenance,
                                                              remaining_cycles_until_end_of_recommended_maintenance)


        if overlapping_intervals:  # if there can be more than one machine under maintenance at the same time

            overlapping_machines = [machine for machines, start, end in overlapping_intervals for machine in machines
                                    if machine != machine_for_separation_position]



            machine_for_separation_position = [machine_for_separation_position] + overlapping_machines

        # divide the current production sequence in two
        first_production_sequence = production_sequence[:min_separation_position]
        second_production_sequence = production_sequence[min_separation_position:]

        return machine_for_separation_position,first_production_sequence, second_production_sequence


def propagate_machine_cycles(machine_operation_information):

    """
        Propagates the last valid cycle number to 'Free' or 'Unavailable' states,
        to ensure continuity in the machine's cycle information.

        Example:

            INPUT
            m1: t9-> cycle_number = 100, production_flag = "Producing", product_label = "A3_4"
                t10-> cycle_number = 0, production_flag = "Free", product_label = None

            OUTPUT
            m1: t9-> cycle_numer = 100, production_flag = "Producing", product_label = "A3_4"
                t10-> cycle_number = 100, production_flag = "Free", product_label = None

    """

    for machine, time_slots_info in machine_operation_information.items():

        last_cycle_number = None

        for time_slot, info in time_slots_info.items():

            if info["production_flag"] == "Producing" or info["production_flag"] == "Maintenance":
                last_cycle_number = info["cycle_number"]

            elif (info["production_flag"] == "Free" or info["production_flag"] == "Unavailable") and last_cycle_number is not None:
                info["cycle_number"] = last_cycle_number

    return


def check_for_maintenance_overlap(remaining_cycles_until_start_of_recommended_maintenance,
                                  remaining_cycles_until_end_of_recommended_maintenance):
    """

        Checks if more than one machine can be under maintenance in the same timeslots,
        by seeing if the recommend maintenance intervals overlap.

    """

    machines = list(remaining_cycles_until_start_of_recommended_maintenance.keys())
    machines_recommended_maintenance_times = {machine: (0, 0) for machine in machines}

    overlapping_intervals = []

    for machine in machines:
        start_time = remaining_cycles_until_start_of_recommended_maintenance[machine][0]
        end_time = remaining_cycles_until_end_of_recommended_maintenance[machine][0]
        machines_recommended_maintenance_times[machine] = (start_time, end_time)

    sorted_intervals = sorted(machines_recommended_maintenance_times.items(),
                              key=lambda x: x[1][0])  # ordered by start time

    current_group = []  # do the overlapping check by groups since there can be overlapping in multiple machines
    current_start, current_end = -1, -1

    for machine, (start_time, end_time) in sorted_intervals:

        if current_group and start_time <= current_end:  # if this machine overlaps with the current group
            current_group.append(machine)
            current_end = max(current_end, end_time)

        else:  # if the machine does not overlap with the current group, save it and start another group
            if current_group:
                overlapping_intervals.append((current_group, current_start, current_end))

            current_group = [machine]
            current_start, current_end = start_time, end_time

    if current_group:
        overlapping_intervals.append((current_group, current_start, current_end))

    overlapping_intervals = [interval for interval in overlapping_intervals if
                             len(interval[0]) > 1]  # filter only intervals with more than one machine for return

    if not overlapping_intervals:
        # print("   No suitable intervals for simultaneous machine maintenance.")
        return

    else:
        # print("   Suitable intervals for simultaneous machine maintenance:", overlapping_intervals)
        return overlapping_intervals


####################################################################################################################################################################################
####################################################################################################################################################################################

def production_simulation(production_requirements_dict, production_sequence, operating_machines_list,
                                      initial_cycles, product_machine_cycles_mapping_dict, maintenance_duration,
                                      s_maintenance_min, s_maintenance_max, survival_dict, logger, optimized_sequence):

    product_counts = {  # to save how many times a product type has been scheduled for a certain machine
        machine: {product: 0 for product in production_requirements_dict} for machine in operating_machines_list}

    time_slot_0 = 0 # assuming that the simulation always starts from time slot 0

    schedule, time_slots = schedule_setup(operating_machines_list)

    machine_end_times = {machine: 0 for machine in operating_machines_list} # to store the time slot when each machine will be available
    machine_cycle_numbers = {machine: initial_cycles.get(machine, 0) for machine in operating_machines_list} # initialize the initial cycle number for each machine based on the initial_cycles dictionary

    scheduled_maintenance_intervals = []

    machine_operation_information = {
        machine: {
            time_slot: {
                "cycle_number": 0,
                "production_flag": "Free",
                "product_label": None
            }
            for time_slot in time_slots
        }
        for machine in operating_machines_list
    }

    first_production_sequence = production_sequence

    # print('\n************************************************************************************************')
    # print(f'   REQUIRED SEQUENCE {first_production_sequence}')
    # print('************************************************************************************************')

    aux_count = 0
    aux_count_machine_maintenance = {machine: 0 for machine in operating_machines_list}

    while first_production_sequence is not None:

        machine_for_separation_position, first_production_sequence, second_production_sequence = divide_production_sequence(product_machine_cycles_mapping_dict, first_production_sequence, operating_machines_list, machine_cycle_numbers,s_maintenance_max, s_maintenance_min, survival_dict)
        # if first_production_sequence and second_production_sequence:
        if first_production_sequence:

            aux_count += 1

            # print('\n-------------------------------------------------------------------')
            # print(f'SIMULATING SEQUENCE {aux_count} {first_production_sequence}')
            # print('-------------------------------------------------------------------')

            for product in first_production_sequence:

                # print(f'\n  ****PRODUCT {product}****')

                product_start_time = time_slot_0

                for machine in operating_machines_list:

                    # print(f'\n     Machine {machine}')

                    production_cycles = product_machine_cycles_mapping_dict[machine].get(product, 0) # number of cycles required for the machine to produce that product

                    if production_cycles > 0: # if the machine is required for the current product

                        current_cycle_number = machine_cycle_numbers[machine]

                        start_time = max(product_start_time, machine_end_times[machine]) # the start time for the machine's operation can only be when the machine is free

                        update_schedule_for_product(schedule, product, machine, start_time, production_cycles, machine_operation_information, current_cycle_number, product_counts)

                        for current_cycle in range(production_cycles):

                            # print(f'     - Machine Cycle Number: {current_cycle_number}')
                            current_cycle_number += 1

                        machine_cycle_numbers[machine] = current_cycle_number # update the machine's "starting" cycle number after it finishes the current product to ensure that the next product starts from the correct cycle number

                        machine_end_times[machine] = start_time + production_cycles # update when the machine will be free / operation ends

                        product_start_time = machine_end_times[machine] # update the starting time slot for the next cycle


            if second_production_sequence is not None:

                maintenance_start_time = max(machine_end_times.values())
                time_slot_0 = maintenance_start_time + maintenance_duration # the next timeslot available for production is after maintenance

                update_schedule_for_maintenance(schedule, maintenance_start_time, machine_for_separation_position, machine_operation_information, operating_machines_list, maintenance_duration, scheduled_maintenance_intervals)

                if isinstance(machine_for_separation_position,list):  # if it's a list <=> multiple machines were under maintenance/repaired
                    for machine in machine_for_separation_position:

                        if machine in machine_cycle_numbers:
                            machine_cycle_numbers[machine] = 1
                            aux_count_machine_maintenance[machine] += 1

                else:  # if only a machine was under maintenance
                    if machine_for_separation_position in machine_cycle_numbers:
                        machine_cycle_numbers[machine_for_separation_position] = 1
                        aux_count_machine_maintenance[machine_for_separation_position] += 1

                first_production_sequence = second_production_sequence

            else:
                break

        # case when the machine needs immediate maintenance before the production starts
        elif machine_for_separation_position  and not first_production_sequence and not second_production_sequence:

            update_schedule_for_maintenance(schedule, time_slot_0, machine_for_separation_position, machine_operation_information, operating_machines_list, maintenance_duration, scheduled_maintenance_intervals)

            machine_for_separation_position = str(machine_for_separation_position)

            if isinstance(machine_for_separation_position, list): # if it's a list <=> multiple machines were under maintenance/repaired
                for machine in machine_for_separation_position:

                    if machine in machine_cycle_numbers:
                        machine_cycle_numbers[machine] = 1
                        aux_count_machine_maintenance[machine] += 1

            else: # if only a machine was under maintenance
                if machine_for_separation_position in machine_cycle_numbers:
                    machine_cycle_numbers[machine_for_separation_position] = 1
                    aux_count_machine_maintenance[machine_for_separation_position] += 1

            time_slot_0 = maintenance_duration
            first_production_sequence = production_sequence
            continue

        else:
            break

    propagate_machine_cycles(machine_operation_information) # update machine's cycles in machine_operation_information
    total_downtime = calculate_downtime(scheduled_maintenance_intervals)

    # ------ NOTA ------
    # esta solução não é a mais robusta pq estou a assumir que qnd as todas as máquinas estão 'Free' ao mesmo
    # tempo é pq a produção acabou (na maneira como o scheduling está agora não há problema, só haveria problema
    # se essa lógica fosse alterada)

    for final_time_slot in machine_operation_information[next(iter(machine_operation_information))].keys():

        # to calculate the total duration of the production, by seeing what is the first time slot where all machines are Free
        all_free = True

        for machine in machine_operation_information:
            if machine_operation_information[machine][final_time_slot]['production_flag'] != 'Free':
                all_free = False
                break

        if all_free:

            final_time_slot = int(final_time_slot[1:])
            final_time_slot = final_time_slot - 1
            break

    if optimized_sequence: # only prints the information for the optimized sequence that was returned by the optimization algorithm

        print('\n   -------------------------')
        print('     SIMULATION STATISTICS')
        print('   -------------------------')

        logger.info('SIMULATION RESULTS')
        logger.info(f'Optimal Production Sequence: {production_sequence}')
        logger.info(' ')

        print_stats_production(production_sequence, production_requirements_dict, final_time_slot, product_machine_cycles_mapping_dict, operating_machines_list, logger)
        print_stats_maintenance(total_downtime, operating_machines_list, aux_count_machine_maintenance, scheduled_maintenance_intervals, logger)
        save_schedule_and_machine_operation_information_excel_files(schedule, final_time_slot, machine_operation_information)
        plot_survival_prob_over_cycles(machine_operation_information, survival_dict, final_time_slot)

    return scheduled_maintenance_intervals, total_downtime

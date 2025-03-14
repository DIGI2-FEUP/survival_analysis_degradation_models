import matplotlib.pyplot as plt
import numpy as np
import datetime

from survival_function_operations import get_survival_prob

plots_folder_path = 'data/plots/'

def plot_survival_prob_over_cycles(machine_operation_information, survival_dict, final_time_slot):

    """
        Plots the survival probability over cycles for all the machines on one graph.
    """

    plt.figure(figsize=(14, 6))

    for machine in machine_operation_information.keys():

        time_slots = []
        survival_probs = []

        for timeslot, information in machine_operation_information[machine].items():

            if int(timeslot[1:]) <= final_time_slot:

                if information['cycle_number'] > 0:
                    survival_prob = get_survival_prob(machine, information['cycle_number'], survival_dict, degree=5)

                else:
                    survival_prob = np.nan

                time_slots.append(timeslot)
                survival_probs.append(survival_prob)

        # for the graph line to continue when the machine is under maintenance
        survival_probs = np.array(survival_probs)
        nans = np.isnan(survival_probs)
        survival_probs[nans] = np.interp(np.flatnonzero(nans), np.flatnonzero(~nans), survival_probs[~nans])

        plt.plot(time_slots, survival_probs, label=machine, marker='')

    tick_positions = range(0, len(time_slots), int(len(time_slots)/50)) # only show timeslot from x in x
    plt.xticks(tick_positions, rotation=25)

    plt.xlabel('Time Slot / Cycle')
    plt.ylabel('Survival Probability')

    plt.title('Survival Probability over Cycles')
    plt.legend(title='Machines')

    plt.grid(True)
    plt.tight_layout()

    simulation_datetime = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    plot_path = f"{plots_folder_path}survival_probability_over_cycles_{simulation_datetime}.png"

    plt.savefig(plot_path)
    print(f'Saved survival probability over cycles plot at \'{plot_path}.png\'.')
    # plt.show()


def print_stats_production(production_sequence, production_requirements_dict, final_time_slot, product_machine_cycles_mapping_dict, operating_machines_list, logger):

    """
        Prints production information :
            - Total produced products
            - Duration of production
            - Number of cycles "used" by each machine
    """

    from simulation_operations import calculate_required_cycle_for_production_sequence

    required_cycles_for_production_sequence = calculate_required_cycle_for_production_sequence(product_machine_cycles_mapping_dict, production_sequence, operating_machines_list)

    print('\n   --- PRODUCTION ---')

    print(f'\n     -Production duration (in cycles): {final_time_slot}')

    logger.info(f'SIMULATION RESULTS - PRODUCTION')
    logger.info(f'  - Production duration (in cycles): {final_time_slot}')

    for machine in operating_machines_list:
        print(f'     -Cycles used by machine {machine}: {required_cycles_for_production_sequence[machine][-1]}')
        logger.info(f'  - Cycles used by machine {machine}: {required_cycles_for_production_sequence[machine][-1]}')

    print(f'     -Total of produced products: {len(production_sequence)}')
    logger.info(f'  - Total of produced products: {len(production_sequence)}')


    for product_type in production_requirements_dict.keys():
        print(f'        -> {product_type}: {production_requirements_dict[product_type]}')
        logger.info(f'      - {product_type}: {production_requirements_dict[product_type]}')

    logger.info(' ')

def print_stats_maintenance(total_downtime, operating_machines_list, aux_count_machine_maintenance, scheduled_maintenance_intervals, logger):

    """
            Prints maintenance information :
                - Duration of production downtime
                - Number of time each machine was under maintenance
                - Intervals where each machine was under maintenance
    """

    print('\n   --- MAINTENANCE ---')

    print(f'\n     -Total production downtime (in cycles): {total_downtime}')

    logger.info(f'SIMULATION RESULTS - MAINTENANCE')
    logger.info(f'  - Total production downtime (in cycles): {total_downtime}')

    for machine in operating_machines_list:
        print(f'     -Number of times machine {machine} was under maintenance: {aux_count_machine_maintenance[machine]}')
        logger.info(f'  - Number of times machine {machine} was under maintenance: {aux_count_machine_maintenance[machine]}')


        for scheduled_machine, (maintenance_start_time, maintenance_end_time) in scheduled_maintenance_intervals:
            if scheduled_machine == machine:
                print(f'        -> from t{maintenance_start_time} to t{maintenance_end_time}')
                logger.info(f'      - from t{maintenance_start_time} to t{maintenance_end_time}')
    logger.info(' ')


def format_duration(seconds):
    """
        Format the result of the optimization duration in seconds, minutes or hours.
    """

    if seconds >= 60:
        return f"{seconds / 60:.2f} minutes"

    if seconds >= 3600:
        return f"{seconds / 3600:.2f} hours"

    else:
        return f"{seconds:.2f} seconds"


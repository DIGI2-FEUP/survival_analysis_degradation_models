import pandas as pd

def schedule_setup(operating_machines_list):

    """
        Initial setup of a scheduling table that allows to check machines availability during production cycles.
    """

    scheduling_table_time_units = 40000 # max value (of columns in an Excel sheet)
    time_slots = [f"t{i}" for i in range(scheduling_table_time_units)]

    schedule = pd.DataFrame(index=operating_machines_list, columns=time_slots)
    schedule[:] = 'Free'

    return schedule, time_slots


def update_schedule_for_product(schedule, product, machine, start_time, operation_duration, machine_operation_information,current_cycle_number, product_counts):

    """
        Update the machine's scheduling table / production
        timeslots based on each product in the production sequence.
    """

    product_count = product_counts[machine].get(product, 0) # keep track how many times this product type has been produced in this machine, example: 1 = means first A0 to be produced, 2 = second A0, ...
    current_cycle_number = current_cycle_number - 1

    for cycle in range(operation_duration): # operation_duration <=> number of cycle required to product the product in a certain machine

        time_slot = f"t{start_time + cycle}"

        current_cycle_number = current_cycle_number + 1
        product_label = f"{product}_{product_count + 1}"  # unique product label like Ax_1, ..., Ax_500, ...

        machine_operation_information[machine][time_slot]['production_flag'] = "Producing"
        machine_operation_information[machine][time_slot]['cycle_number'] = current_cycle_number
        machine_operation_information[machine][time_slot]['product_label'] = product_label

        schedule.at[machine, time_slot] = product_label

    product_counts[machine][product] = product_count + 1

def update_schedule_for_maintenance(schedule, maintenance_start_time, machine_under_maintenance, machine_operation_information, operating_machines_list, maintenance_duration, scheduled_maintenance_intervals):

    """
            Update the machine's scheduling table / production
            timeslots based on the maintenance intervals of each machine.
    """

    if isinstance(machine_under_maintenance, str):
        machine_under_maintenance = [machine_under_maintenance] # since machine_under_maintenance can either be 1 or multiple, always treat it as list

    for cycle in range(maintenance_duration):

        time_slot = f"t{maintenance_start_time + cycle}"

        for machine in machine_under_maintenance: # update for each machine under maintenance

            schedule.at[machine, time_slot] = "Maintenance"
            machine_operation_information[machine][time_slot]['production_flag'] = "Maintenance"
            machine_operation_information[machine][time_slot]['cycle_number'] = -1  # -1 to signal maintenance
            machine_operation_information[machine][time_slot]['product_label'] = None

        for machine in operating_machines_list: # for the other machines (can't be producing)

            if machine not in machine_under_maintenance:  # only if the machine is not under maintenance
                schedule.at[machine, time_slot] = "Unavailable"
                machine_operation_information[machine][time_slot]['production_flag'] = "Unavailable"

    for machine in machine_under_maintenance:
        scheduled_maintenance_intervals.append((machine, (maintenance_start_time, maintenance_start_time+maintenance_duration-1)))


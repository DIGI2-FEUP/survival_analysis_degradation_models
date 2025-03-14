
def user_input_simulation_interface(product_machine_cycles_mapping_dict,maintenance_duration, cycle_duration,
                                    initial_cycles, s_maintenance_min, s_maintenance_max):
    """
            Displays the current simulation parameters and allows users to edit them. The parameters include:
                - Required production cycles per product per machine -> specifies the number of cycles (or operations)
                                                                        required for each product type on specific machines
                                                                        Example:  {"m1": {"A0": 50, "A1": 2, "A2": 8, "A3": 1},
                                                                                   "m2": {"A0": 12, "A1": 2, "A2": 10, "A3": 1}}
                - Maintenance duration
                - Initial cycles for each machine -> the number of cycles a machine has run since the last maintenance,
                                                     starting at 0 and increasing with each produced product
                - Minimum and maximum survival probability for maintenance

            The function also asks/requires the user to input production requirements for the simulation, such as
                - Available machines
                - Product types and quantities

"""

    print('\n-------------------------------------------------')
    print('     SIMULATION PARAMETERS')
    print('-------------------------------------------------')

    print('\n--- CURRENT PRODUCTION SIMULATION PARAMETERS ---')

    print('\n 1) Required production cycles per product per machine:')
    for machine, products in product_machine_cycles_mapping_dict.items():
        product_cycles = ', '.join([f'{product}: {cycles}' for product, cycles in products.items()])
        print(f'        {machine} - {product_cycles}')

    print(' 2) Maintenance duration (in cycles):', maintenance_duration)
    print(' 3) Cycle duration:', cycle_duration)
    print(' 4) Initial cycles for each machine:', initial_cycles)
    print(' 5) Minimum survival probability for maintenance:', s_maintenance_min)
    print(' 6) Maximum survival probability for maintenance:', s_maintenance_max)

    product_machine_cycles_mapping_dict, maintenance_duration, cycle_duration, initial_cycles, s_maintenance_min, s_maintenance_max = user_input_edit_production_simulation_parameters(product_machine_cycles_mapping_dict,
                                                                                                                                                                        maintenance_duration, cycle_duration,
                                                                                                                                                                        initial_cycles, s_maintenance_min,
                                                                                                                                                                        s_maintenance_max)

    print('\n-------------------------------------------------')
    print('     PRODUCTION REQUIREMENTS')
    print('-------------------------------------------------')
    print('(if there are multiple inputs, separate them using commas)')

    # get the available machines for production
    operating_machines_list = input('\nEnter the available machines for operation: ').strip().split(',')
    operating_machines_list = [machine.lower().strip() for machine in operating_machines_list]

    # check if machines are mapped in the dictionary that has the number of cycles required
    # for each product type on specific machines
    for machine in operating_machines_list:

        if machine not in product_machine_cycles_mapping_dict:

            print(f"Machine '{machine}' is not mapped with production cycles. "
                  f"Edit the current mapping or remove '{machine}' from the input.")
            return

    # get the product types to produce
    product_types_requirements_list = input('Enter the product types to be produced: ').strip().split(',')
    product_types_requirements_list = [product_type.upper().strip() for product_type in product_types_requirements_list]

    for product_type in product_types_requirements_list:

        unavailable_machines = []

        for machine in product_machine_cycles_mapping_dict:

            # check if the machine doesn't have a cycle mapping for the current product type
            # if so, add the machine to the list of unavailable machines
            if product_type not in product_machine_cycles_mapping_dict.get(machine, {}):
                unavailable_machines.append(machine)

            # check if the current product type requires a specific machine that is not in the available machines list
            if product_type in product_machine_cycles_mapping_dict[machine] and machine not in operating_machines_list:
                
                print(f"  Warning: Product '{product_type}' requires machine '{machine}',which is not available for operation.")
                return

        # for cases where none of the available machines have a production cycle mapping for the current product type
        if len(unavailable_machines) == len(operating_machines_list):
            
            print(f"  - No production information available for product '{product_type}' on any available machine.")
            return

        # for cases where some available machines don't have production cycle mapping for the current product type
        elif unavailable_machines:
            
            print( f"  - The following machines don't have the production mapping for product {product_type}: {', '.join(unavailable_machines)}.")
            return

    production_requirements_dict = {}

    # get the number of unit of each product to be produced and saves in the production requirements dictionary
    for product_type in product_types_requirements_list:
        while True:

            try:
                product_quantity = int(input(f'  How many units of product "{product_type}"? '))
                production_requirements_dict[product_type] = product_quantity
                break

            except ValueError:
                print("Invalid input.")


def user_input_edit_production_simulation_parameters(product_machine_cycles_mapping_dict, maintenance_duration, cycle_duration,
                                                     initial_cycles, s_maintenance_min, s_maintenance_max):
    """
          Allows the user to edit multiple simulation parameters and saves the changes.
          If any parameter is updated, the function displays the updated parameter values at the end.
    """

    changes_made = False

    while True:

        if input('\n   Edit any of the parameters [y/n]? ').lower() == 'y':

            parameter_to_edit = input( '   Which parameter would you like to edit? ')
            parameter_to_edit = parameter_to_edit.strip()

            # edit product_machine_cycles_mapping_dict
            if parameter_to_edit == '1':
                print('\n      Editing production cycles mapping...')

                while True:

                    print("\n      Current machines in the mapping:", list(product_machine_cycles_mapping_dict.keys()))
                    machine_to_edit = input("      Enter the machine to edit (or type 'new' to add a machine or 'stop' to stop): ").strip()

                    if machine_to_edit.lower() == 'stop': break

                    if machine_to_edit.lower() == 'new':

                        new_machine = input("Enter the name of the new machine: ").strip()
                        product_machine_cycles_mapping_dict[new_machine] = {}
                        print(f"       Machine '{new_machine}' added. Please enter production cycles for each product.")

                        while True:
                            new_product = input("       Enter product type (or press ENTER to stop adding products): ").strip()

                            if not new_product: break

                            try:
                                new_cycles = int( input(f"       Enter required production cycles for product '{new_product}': "))
                                product_machine_cycles_mapping_dict[new_machine][new_product] = new_cycles
                                changes_made = True

                            except ValueError: print("Invalid input.")

                    elif machine_to_edit in product_machine_cycles_mapping_dict:

                        print(f'\n      -Editing cycles for machine {machine_to_edit}:')

                        for product_type, current_cycles in product_machine_cycles_mapping_dict[machine_to_edit].items():
                            print(f'\n        Current cycles for product "{product_type}": {current_cycles}')

                            try:
                                required_cycles = int(input(f'        Enter the new number of required production cycles (or press ENTER to keep {current_cycles}): ') or current_cycles)

                                if required_cycles != current_cycles:
                                    product_machine_cycles_mapping_dict[machine_to_edit][product_type] = required_cycles
                                    changes_made = True

                            except ValueError: print("Invalid input. Keeping the current value.")

                    else:
                        print(f"Machine '{machine_to_edit}' not found.")

                print('    Updated!')

            # edit maintenance_duration
            elif parameter_to_edit == '2':
                print(f'\n    Current maintenance_duration: {maintenance_duration}')

                new_value = int(input('    Enter the new maintenance duration (or press ENTER to keep current): ') or maintenance_duration)

                if new_value != maintenance_duration:
                    maintenance_duration = new_value
                    changes_made = True

                print('    Updated!')

            # edit cycle_duration
            elif parameter_to_edit == '3':
                print(f'\n    Current cycle_duration: {cycle_duration}')

                new_value = float(input('    Enter the new cycle duration (or press ENTER to keep current): ') or cycle_duration)

                if new_value != cycle_duration:
                    cycle_duration = new_value
                    changes_made = True

                print('    Updated!')

            # edit initial_cycles
            elif parameter_to_edit == '4':

                for machine, current_cycles in initial_cycles.items():
                    print(f'\n    Current initial cycles for machine {machine}: {current_cycles}')

                    try:
                        new_cycles = int(input(f'    Enter the new number of initial cycles for machine {machine} (or press ENTER to keep {current_cycles}): ') or current_cycles)

                        if new_cycles != current_cycles:
                            initial_cycles[machine] = new_cycles
                            changes_made = True

                    except ValueError: print("    Invalid input. Keeping the current value.")

                print('    Updated!')

            # edit s_maintenance_min
            elif parameter_to_edit == '5':
                print(f'\n    Current s_maintenance_min: {s_maintenance_min}')

                new_value = float(input('    Enter the new minimum survival probability (or press ENTER to keep current): ') or s_maintenance_min)

                if new_value != s_maintenance_min:
                    s_maintenance_min = new_value
                    changes_made = True

                print('    Updated!')

            # edit s_maintenance_max
            elif parameter_to_edit == '6':
                print(f'\n    Current s_maintenance_max: {s_maintenance_max}')

                new_value = float(input('    Enter the new maximum survival probability (or press ENTER to keep current): ') or s_maintenance_max)

                if new_value != s_maintenance_max:
                    s_maintenance_max = new_value
                    changes_made = True

                print('    Updated!')

            # if the user doesn't enter 1, 2, 3, 4, 5 or 6
            else:
                print('    Invalid parameter.')

            # allow the user to edit multiple parameters, one at a time
            continue_editing = input('\n   Edit another parameter [y/n]? ').lower()

            if continue_editing != 'y':
                break

        else: # if the user doesn't want to edit any parameter
            break

    if changes_made: # only displays the new parameters if any changes were made

        print('\n--- UPDATED PRODUCTION SIMULATION PARAMETERS ---')

        print('\n 1) Required production cycles per product per machine:')
        for machine, products in product_machine_cycles_mapping_dict.items():
            product_cycles = ', '.join([f'{product}: {cycles}' for product, cycles in products.items()])
            print(f'        {machine} - {product_cycles}')

        print(' 2) Maintenance duration (in cycles):', maintenance_duration)
        print(' 3) Cycle duration:', cycle_duration)
        print(' 4) Initial cycles for each machine:', initial_cycles)
        print(' 5) Minimum survival probability for maintenance:', s_maintenance_min)
        print(' 6) Maximum survival probability for maintenance:', s_maintenance_max)

    else:
        print('   No changes made to the parameters.')

    return product_machine_cycles_mapping_dict, maintenance_duration, cycle_duration, initial_cycles, s_maintenance_min, s_maintenance_max

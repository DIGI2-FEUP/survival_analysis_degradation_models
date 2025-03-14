import os
import math
import pandas as pd

data_folder_path = 'data/'

def save_schedule_and_machine_operation_information_excel_files(schedule, final_time_slot, machine_operation_information):

    """
        Save the schedule table and the production information in Excel files.
        The production information has the following structure:

        -> Machine 'mx' (row)
            -> Timeslot 'ty' (main column)
                -> Product (sub-column 1): the type of ID of the product being produced,
                                                    ex: A0_4 = the 4th A0 product being produced
                -> Cycle (sub-column 2): the current cycle number of that machine
                -> State (sub-column 3): "Producing"/"Free"/"Maintenance"/"Unavailable"
    """

    final_time_slot_schedule_index = schedule.columns.get_loc('t' + str(final_time_slot))
    schedule = schedule.iloc[:, :final_time_slot_schedule_index + 1]

    schedule_file = os.path.join(data_folder_path, 'production_schedule.xlsx')

    if len(schedule.columns) > 16384: # max number of columns supported in an Excel sheet


        filenames = divide_large_excel_files(schedule, 'production_schedule')
        print(f'\nSaved production scheduling table at \'{filenames}\'.')

    else:
        print(f'\nSaved production scheduling table at \'{schedule_file}\'.')
        schedule.to_excel(schedule_file)

    # transform machine_operation_information dict into a df save it in an Excel
    machine_operation_information_file = os.path.join(data_folder_path, 'machine_operation_information.xlsx')

    # ------ NOTA ------
    # esta solução não é a mais robusta pq estou a assumir que qnd as todas as máquinas estão 'Free' ao mesmo
    # tempo é pq a produção acabou (na maneira como o scheduling está agora não há problema, só haveria problema
    # se essa lógica fosse alterada)

    machine_operation_information = {
        machine: {
            time_slot: data
            for time_slot, data in machine_info.items()
            if int(time_slot[1:]) < final_time_slot
        }
        for machine, machine_info in machine_operation_information.items()
    }

    df_machine_operation_information = transform_machine_operation_information_to_df(machine_operation_information)

    if len(df_machine_operation_information.columns) > 16384: # max number of columns supported in an Excel sheet
        filenames = divide_large_excel_files(df_machine_operation_information, 'machine_operation_information')
        print(f'\nSaved production scheduling table at \'{filenames}\'.')

    else:
        df_machine_operation_information.to_excel(machine_operation_information_file)
        print(f'Saved production information at \'{machine_operation_information_file}\'.')


def transform_machine_operation_information_to_df(machine_operation_information):

    """
        Transforms machine_operation_information (a nested dictonary) into a DF with
        multi-index columns, where the rows are 'Machines' and the columns are 'TimeSlot' and 'Cycle', 'State', 'Product'.

        Example:

            |____________t0___________|____________t1___________| ...
            | Cycle | State | Product | Cycle | State | Product |
            |___________________________________________________|
         |m1|   1   | Free  |   None  |   1   | Free  |   None  |
         |m2|   4   | Prod. |   A0_1  |   5   | Prod. |   A0_1  |
         ...
    """

    df_time_slots = list(next(iter(machine_operation_information.values())).keys())
    attributes = ['Product', 'State', 'Cycle']

    columns = pd.MultiIndex.from_product([df_time_slots, attributes])

    df_machine_operation_information = pd.DataFrame(index=machine_operation_information.keys(), columns=columns)

    for machine, data in machine_operation_information.items():

        for time_slot, values in data.items():
            cycle_number = values['cycle_number']
            df_machine_operation_information.at[machine, (time_slot, 'Cycle')] = cycle_number

            production_flag = values['production_flag']
            df_machine_operation_information.at[machine, (time_slot, 'State')] = production_flag

            product_label = values['product_label']
            df_machine_operation_information.at[machine, (time_slot, 'Product')] = product_label

    return df_machine_operation_information

def divide_large_excel_files(df, filename):

    """
        Divides and saves DF's with more than 16384 columns (max number of Excel columns in one sheet) into multiple files.
    """

    filenames = []

    max_columns = 16384
    total_columns = len(df.columns)

    number_of_files = math.ceil(total_columns / max_columns)
    starting_column = 0

    # flatten in case of multi-index columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(map(str, col)).strip() for col in df.columns]

    for file_number in range(number_of_files):

        end_column = min(starting_column + max_columns, total_columns)
        divided_df = df.iloc[:, starting_column:end_column]

        divided_df_filename = os.path.join(data_folder_path, f"{filename}_part_{file_number + 1}.xlsx")
        divided_df.to_excel(divided_df_filename, index=True)

        starting_column = end_column
        filenames.append(divided_df_filename)

    return filenames



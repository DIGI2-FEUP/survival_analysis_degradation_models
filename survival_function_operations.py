import numpy as np
import pandas as pd

base_survival_function_path = 'data/base_survival_function/base_survival_function.csv'
base_survival_function = pd.read_csv(base_survival_function_path)

def starting_survival_function_data(machine, survival_dict):

    """
        Filter the required survival data based on the initial cycle number of each machine.
    """

    machine_survival_function = base_survival_function.copy()

    machine_survival_function_dict = dict(zip(machine_survival_function['prod_idx'], machine_survival_function['surv_prob']))
    survival_dict[machine] = machine_survival_function_dict

def survival_function(machine, degree, survival_dict):

    """
        Polynomial regression to approximate the survival function for all points/cycles.
    """

    survival_data = survival_dict[machine]
    prod_idx = np.array(list(survival_data.keys()))
    surv_prob = np.array(list(survival_data.values()))

    poly_coeffs = np.polyfit(prod_idx, surv_prob, degree)

    return poly_coeffs

def get_survival_prob(machine, cycle, survival_dict, degree=5):

    """
        Returns the survival probability for a given cycle, for a given machine.
    """

    poly_coeffs = survival_function(machine, degree, survival_dict)
    survival_prob = max(0, min(1, np.polyval(poly_coeffs, cycle)))

    return survival_prob


def get_survival_cycles(machine, target_prob, survival_dict, degree=5):

    """
        Returns the closest integer cycle number for a given survival probability, for a given machine.
        The result is always rounded down to the nearest integer.
    """

    poly_coeffs = survival_function(machine, degree, survival_dict)
    poly_coeffs[-1] -= target_prob

    roots = np.roots(poly_coeffs)
    real_roots = [root.real for root in roots if np.isreal(root) and root.real >= 0]

    if real_roots:
        return int(min(real_roots))

    else:
        prod_idx, surv_prob, _ = survival_function(machine, degree, survival_dict)
        closest_cycle = min(prod_idx,key=lambda c: abs(get_survival_prob(machine, c, survival_dict, degree) - target_prob))

        return int(closest_cycle)




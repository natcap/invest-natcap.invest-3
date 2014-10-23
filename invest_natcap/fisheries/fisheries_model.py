import logging

import numpy as np

LOGGER = logging.getLogger('FISHERIES')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')


def initialize_vars(vars_dict):
    '''Initializes variables

    **Example Output**
    vars_dict = {
        # (other items)
        ...
        'Survtotalfrac': np.array([...]),  # Index Order: region, sex, class
        'G_survtotalfrac': np.array([...]),  # (same)
        'P_survtotalfrac': np.array([...]),  # (same)
        'N_all': np.array([...]),  # Index Order: time, region, sex, class
    }
    '''
    # Initialize derived parameters
    # Survtotalfrac, P_survtotalfrac, G_survtotalfrac, N_all
    vars_dict['Survtotalfrac'] = _calc_survtotalfrac(vars_dict)

    if vars_dict['population_type'] == 'Stage-Based':
        G, P = _calc_p_g_survtotalfrac(vars_dict)
        vars_dict['G_survtotalfrac'] = G
        vars_dict['P_survtotalfrac'] = P

    t = vars_dict['total_timesteps']
    x = len(vars_dict['Regions'])  # Region
    s = vars_dict['sexsp']  # Sex
    a = len(vars_dict['Classes'])  # Class
    vars_dict['N_all'] = np.ndarray([t, x, s, a])

    return vars_dict


def set_recru_func(vars_dict):
    '''
    Creates optimized recruitment function

    rec_eq_str, Matu, Weight, Fec, fixed, alpha, beta, sexsp
    '''
    def create_Spawners(Matu, Weight):
        return lambda N_prev: (N_prev * Matu * Weight).sum()

    def create_BH(alpha, beta, sexsp, Matu, Weight):
        spawners = create_Spawners(Matu, Weight)
        return lambda N_prev: ((alpha * spawners(
            N_prev) / (beta + spawners(N_prev)))) / sexsp

    def create_Ricker(alpha, beta, sexsp, Matu, Weight):
        spawners = create_Spawners(Matu, Weight)
        return lambda N_prev: (alpha * spawners(
            N_prev) * (np.e ** (-beta * spawners(N_prev)))) / sexsp

    def create_Fecundity(Fec, sexsp, Matu):
        return lambda N_prev: (N_prev * Matu * Fec) / sexsp

    def create_Fixed(fixed, sexsp):
        return lambda N_prev: fixed / sexsp

    sexsp = vars_dict['sexsp']

    # Initialize Weight vector according to spawn_units
    if vars_dict['spawn_units'] == "Weight":
        Weight = vars_dict['Weight']
    else:
        Weight = np.ones([sexsp, len(vars_dict['Classes'])])

    # Create Recruitment Function
    if vars_dict['recru_func'] == "Beverton-Holt":
        alpha = vars_dict['alpha']
        beta = vars_dict['beta']
        Matu = vars_dict['Maturity']
        return create_BH(alpha, beta, sexsp, Matu, Weight)
    elif vars_dict['recru_func'] == "Ricker":
        alpha = vars_dict['alpha']
        beta = vars_dict['beta']
        Matu = vars_dict['Maturity']
        return create_Ricker(alpha, beta, sexsp, Matu, Weight)
    elif vars_dict['recru_func'] == "Fecundity":
        Fec = vars_dict['Fecundity']
        Matu = vars_dict['Maturity']
        return create_Fecundity(Fec, sexsp, Matu)
    elif vars_dict['recru_func'] == "Fixed":
        fixed = vars_dict['total_recur_recruits']
        return create_Fixed(fixed, sexsp)
    else:
        LOGGER.error("Could not determine correct recruitment function")


def set_harvest_func(vars_dict):
    '''
    '''
    # Calculate Harvest
    # Calculate Valuation
    pass


def set_init_cond_func(vars_dict, recru_func):
    '''
    '''
    pass


def set_cycle_func(vars_dict, recru_func, harvest_func):
    '''
    '''
    pass


def run_population_model(vars_dict, init_cond_func, cycle_func):
    '''
    '''
    pass


# Helper functions for initializing derived variables
def _calc_survtotalfrac(vars_dict):
    '''Implements:
    S_xsa = surv_xsa * (1 - Exploitationfraction_x * Vulnfishing_sa)

    :return: Survtotalfrac
    :rtype: np.array
    '''
    S_nat = vars_dict['Survnaturalfrac']
    E = vars_dict['Exploitationfraction']
    V = vars_dict['Vulnfishing']

    I = []
    for x in E:
        I.append(x * V)
    I = np.array(I)

    S_tot = S_nat * (1 - I)

    if np.isnan(S_tot).any():
        LOGGER.warning("Survival Matrix Contains NaN Values")

    return S_tot


def _calc_p_g_survtotalfrac(vars_dict):
    '''Implements:
    G_xsa = (S_xsa ** D_sa) * ((1 - S_xsa) / (1 - S_xsa ** D_sa))

    P_xsa = S_xsa * ((1 - S_xsa ** (D_sa - 1)) / (1 - S_xsa ** D_sa))
    '''
    S_tot = vars_dict['Survtotalfrac']
    D_sa = vars_dict['Duration']

    I = S_tot ** D_sa
    G = I * ((1 - S_tot) / (1 - I))

    I_2 = S_tot ** (D_sa - 1)
    P = S_tot * ((1 - I_2) / (1 - I))

    if (np.isnan(G).any() or np.isnan(P).any()):
        LOGGER.warning(
            "Stage-based Survival Matrices Contain NaN Values")

    return G, P

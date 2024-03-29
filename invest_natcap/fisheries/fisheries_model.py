'''
The Fisheries Model module contains functions for running the model

Variable Suffix Notation:
t: time
x: area/region
a: age/class
s: sex
'''

import logging

import numpy as np

LOGGER = logging.getLogger('invest_natcap.fisheries.model')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')


def initialize_vars(vars_dict):
    '''
    Initializes variables for model run

    Args:
        vars_dict (dictionary): verified arguments and variables

    Returns:
        vars_dict (dictionary): modified vars_dict with additional variables

    Example Returns::

        vars_dict = {
            # (original vars)

            'Survtotalfrac': np.array([...]),  # a,s,x
            'G_survtotalfrac': np.array([...]),  # (same)
            'P_survtotalfrac': np.array([...]),  # (same)
            'N_tasx': np.array([...]),  # Index Order: t,a,s,x
            'H_tx': np.array([...]), # t,x
            'V_tx': np.array([...]), # t,x
            'Spawners_t': np.array([...]),
        }
    '''
    # Initialize derived parameters
    # Survtotalfrac, P_survtotalfrac, G_survtotalfrac, N_tasx
    vars_dict['Survtotalfrac'] = _calc_survtotalfrac(vars_dict)
    vars_dict['G_survtotalfrac'] = None
    vars_dict['P_survtotalfrac'] = None

    if vars_dict['population_type'] == 'Stage-Based':
        G, P = _calc_p_g_survtotalfrac(vars_dict)
        # Swap axes for easier class-based math in model run
        vars_dict['G_survtotalfrac'] = G.swapaxes(0, 2)
        vars_dict['P_survtotalfrac'] = P.swapaxes(0, 2)

    # Swap axes for easier class-based math in model run
    vars_dict['Survtotalfrac'] = vars_dict['Survtotalfrac'].swapaxes(0, 2)
    vars_dict['Survnaturalfrac'] = vars_dict['Survnaturalfrac'].swapaxes(0, 2)

    t = vars_dict['total_timesteps']
    x = len(vars_dict['Regions'])  # Region
    s = vars_dict['sexsp']  # Sex
    a = len(vars_dict['Classes'])  # Class
    vars_dict['N_tasx'] = np.zeros([t, a, s, x])
    vars_dict['H_tx'] = np.zeros([t, x])
    vars_dict['V_tx'] = np.zeros([t, x])
    vars_dict['Spawners_t'] = np.zeros([t])

    return vars_dict


# Helper functions for initializing derived variables
def _calc_survtotalfrac(vars_dict):
    '''
    Implements the equation
        S_xsa = surv_xsa * (1 - Exploitationfraction_x * Vulnfishing_sa)

    Args:
        vars_dict (dictionary)

    Returns:
        Survtotalfrac (np.ndarray)
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
    '''
    Implements the equations
        G_xsa = (S_xsa ** D_sa) * ((1 - S_xsa) / (1 - S_xsa ** D_sa))

        P_xsa = S_xsa * ((1 - S_xsa ** (D_sa - 1)) / (1 - S_xsa ** D_sa))

    Args:
        vars_dict (dictionary)

    Returns:
        G (np.ndarray)

        P (np.ndarray)
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


def set_recru_func(vars_dict):
    '''
    Creates recruitment function that calculates the number of recruits for
    class 0 at time t for each region (currently sex agnostic). Also
    returns number of spawners

    Args:
        vars_dict (dictionary)

    Returns:
        rec_func (function): recruitment function

    Example Output of Returned Recruitment Function::

        N_next[0], spawners = rec_func(N_prev)
    '''
    sexsp = vars_dict['sexsp']
    LarvDisp = vars_dict['Larvaldispersal']

    # Initialize Weight vector according to spawn_units
    if vars_dict['spawn_units'] == "Weight":
        Weight = vars_dict['Weight']
    else:
        Weight = np.ones([sexsp, len(vars_dict['Classes'])])

    alpha = vars_dict['alpha']
    beta = vars_dict['beta']
    Matu = vars_dict['Maturity']
    Fec = vars_dict['Fecundity']
    fixed = vars_dict['total_recur_recruits']

    def spawners(N_prev):
        return (N_prev * Matu * Weight).sum()

    def rec_func_BH(N_prev):
        N_0 = (LarvDisp * ((alpha * spawners(
            N_prev) / (beta + spawners(N_prev)))) / sexsp)
        return (N_0, spawners(N_prev))

    def rec_func_Ricker(N_prev):
        N_0 = (LarvDisp * (alpha * spawners(N_prev) * (
            np.e ** (-beta * spawners(N_prev)))) / sexsp)
        return (N_0, spawners(N_prev))

    def rec_func_Fecundity(N_prev):
        N_0 = (LarvDisp * (N_prev * Matu * Fec).sum() / sexsp)
        return (N_0, spawners(N_prev))

    def rec_func_Fixed(N_prev):
        N_0 = LarvDisp * fixed / sexsp
        return (N_0, None)

    # Create Recruitment Function
    if vars_dict['recruitment_type'] == "Other":
        try:
            rec_func = vars_dict['recruitment_func']
            assert(hasattr(rec_func, '__call__'))

            # Test function
            N_prev = np.ones([len(vars_dict['Classes']), sexsp, len(
                vars_dict['Regions'])]).swapaxes(0, 2)
            N_0, spawn = rec_func(N_prev)
            assert(type(spawn) is np.float64)
            assert(N_0.shape == (len(vars_dict['Regions']),))
            return rec_func

        except Exception, e:
            LOGGER.error("User-defined recruitment function could not be validated.")
            raise ValueError

    elif vars_dict['recruitment_type'] == "Beverton-Holt":
        return rec_func_BH
    elif vars_dict['recruitment_type'] == "Ricker":
        return rec_func_Ricker
    elif vars_dict['recruitment_type'] == "Fecundity":
        return rec_func_Fecundity
    elif vars_dict['recruitment_type'] == "Fixed":
        return rec_func_Fixed
    else:
        LOGGER.error("Could not determine correct recruitment function")
        raise ValueError


def set_init_cond_func(vars_dict):
    '''
    Creates a function to set the initial conditions of the model

    Args:
        vars_dict (dictionary): variables

    Returns:
        init_cond_func (lambda function): initial conditions function

    Example Return Array::

        N_asx = np.ndarray([...])
    '''
    S = vars_dict['Survtotalfrac']  # S_asx
    LarvDisp = vars_dict['Larvaldispersal']
    sexsp = vars_dict['sexsp']
    total_init_recruits = vars_dict['total_init_recruits']
    num_regions = len(vars_dict['Regions'])
    num_classes = len(vars_dict['Classes'])

    def age_based_init_cond():
        '''
        Returns:
            N_0_asx (np.ndarray): initial numbers
        '''

        N_0 = np.zeros([num_classes, sexsp, num_regions])

        N_0[0] = LarvDisp * total_init_recruits / sexsp

        for i in range(1, num_classes-1):
            N_0[i] = N_0[i-1] * S[i-1]

        if len(N_0) > 1:
            N_0[-1] = (N_0[-2] * S[-2]) / (1 - S[-1])

        return N_0

    def stage_based_init_cond():
        '''
        Returns:
            N_0_asx (np.ndarray): initial numbers
        '''
        N_0 = np.zeros([num_classes, sexsp, num_regions])

        N_0[0] = LarvDisp * total_init_recruits / sexsp
        N_0[1:] = 1

        return N_0

    if vars_dict['population_type'] == 'Age-Based':
        return age_based_init_cond
    elif vars_dict['population_type'] == 'Stage-Based':
        return stage_based_init_cond
    else:
        LOGGER.error(
            "Could not determine which initial_condition function to use")
        raise ValueError


def set_cycle_func(vars_dict, rec_func):
    '''
    Creates a function to run a single cycle in the model

    Args:
        vars_dict (dictionary)

        rec_func (lambda function): recruitment function

    Example Output of Returned Cycle Function::

        N_asx = np.array([...])
        spawners = <int>

        N_next, spawners = cycle_func(N_prev)
    '''
    S = vars_dict['Survtotalfrac']  # S_asx
    P = vars_dict['P_survtotalfrac']  # P_asx
    G = vars_dict['G_survtotalfrac']  # G_asx
    num_classes = len(vars_dict['Classes'])
    Migration = vars_dict['Migration']

    def age_based_cycle_func(N_prev):
        '''
        Computes an Age-Based Time Step

        Args:
            N_prev (np.ndarray): previous cycle numbers

        Returns:
            N_next (np.ndarray): next cycle numbers

            Spawners (np.array): spawners by region
        '''
        N_next = np.ndarray(N_prev.shape)

        N_prev_xsa = N_prev.swapaxes(0, 2)
        N_next_0_xsa, spawners = rec_func(N_prev_xsa)
        N_next[0] = N_next_0_xsa.swapaxes(0, 2)

        for i in range(1, num_classes):
            N_next[i] = np.array(map(lambda x: Migration[i-1].dot(
                x), N_prev[i-1]))[:, 0, :] * S[i-1]

        if len(N_prev) > 1:
            N_next[-1] = N_next[-1] + np.array(map(lambda x: Migration[-1].dot(
                x), N_prev[-1]))[:, 0, :] * S[-1]

        return N_next, spawners

    def stage_based_cycle_func(N_prev):
        '''
        Computes a Stage-Based Time Step

        Args:
            N_prev (np.ndarray): previous cycle numbers

        Returns:
            N_next (np.ndarray): next cycle numbers

            Spawners (np.array): spawners by region
        '''
        N_next = np.ndarray(N_prev.shape)

        N_prev_xsa = N_prev.swapaxes(0, 2)
        N_next_0_xsa, spawners = rec_func(N_prev_xsa)
        N_next[0] = N_next_0_xsa.swapaxes(0, 2)

        N_next[0] = N_next[0] + np.array(Migration[0].dot(N_prev[0])) * S[0]

        for i in range(1, num_classes):
            G_comp = np.array(map(lambda x: Migration[i-1].dot(
                x), N_prev[i-1]))[:, 0, :] * G[i-1]
            P_comp = np.array(map(lambda x: Migration[i].dot(
                x), N_prev[i]))[:, 0, :] * P[i]
            N_next[i] = G_comp + P_comp

        return N_next, spawners

    if vars_dict['population_type'] == 'Age-Based':
        return age_based_cycle_func
    elif vars_dict['population_type'] == 'Stage-Based':
        return stage_based_cycle_func
    else:
        LOGGER.error(
            "Could not determine which initial_condition function to use")
        raise ValueError


def set_harvest_func(vars_dict):
    '''
    Creates harvest function that calculates the given harvest and valuation
    of the fisheries population over each time step for a given region.
    Returns None if harvest isn't selected by user.

    Example Outputs of Returned Harvest Function::

        H_x, V_x = harv_func(N_tasx)

        H_x = np.array([3.0, 4.5, 2.5, ...])
        V_x = np.array([6.0, 9.0, 5.0, ...])

    '''
    sexsp = vars_dict['sexsp']
    frac_post_process = 0.0
    unit_price = 0

    if vars_dict['val_cont']:
        frac_post_process = vars_dict['frac_post_process']
        unit_price = vars_dict['unit_price']

    # Initialize Weight vector according to harvest_units
    if vars_dict['harvest_units'] == "Weight":
        Weight = vars_dict['Weight']
    else:
        Weight = np.ones([sexsp, len(vars_dict['Classes'])])

    E = vars_dict['Exploitationfraction']
    V = vars_dict['Vulnfishing']

    I = []
    for x in E:
        I.append(x * V)
    I = np.array(I)

    def harv_func(N_asx):
        '''
        Compute harvest and valuation

        Args:
            N_asx (np.ndarray)

        Returns:
            H_x (np.ndarray): Harvest by region

            V_x (np.ndarray): Value by region
        '''
        N_xsa = N_asx.swapaxes(0, 2)
        H_xsa = N_xsa * I * Weight
        H_x = np.array(map(lambda x: x.sum(), H_xsa))
        V_x = H_x * (frac_post_process * unit_price)
        return H_x, V_x

    return harv_func


def run_population_model(vars_dict, init_cond_func, cycle_func, harvest_func):
    '''Runs the model

    Args:
        vars_dict (dictionary)

        init_cond_func (lambda function): sets initial conditions

        cycle_func (lambda function): computes numbers for the next time step

        harvest_func (lambda function): computes harvest and valuation

    Returns:
        vars_dict (dictionary)

    Example Returned Dictionary::

        {
            # (other items)
            ...
            'N_tasx': np.array([...]),  # Index Order: time, class, sex, region
            'H_tx': np.array([...]),  # Index Order: time, region
            'V_tx': np.array([...]),  # Index Order: time, region
            'Spawners_t': np,array([...]),
            'equilibrate_timestep': <int>,
        }
    '''
    N_tasx = vars_dict['N_tasx']
    H_tx = vars_dict['H_tx']
    V_tx = vars_dict['V_tx']
    Spawners_t = vars_dict['Spawners_t']
    equilibrate_timestep = False
    subset_size = 10

    # Set Initial Conditions for Population
    N_tasx[0] = init_cond_func()

    # Run Cycles
    for i in range(0, len(N_tasx)-1):
        # Run Harvest and Check Equilibrium for Current Population
        # Consider Wrapping this into a function
        if harvest_func:
            H_x, V_x = harvest_func(N_tasx[i])
            H_tx[i] = H_x
            V_tx[i] = V_x
        if not equilibrate_timestep and i >= subset_size and _is_equilibrated(H_tx, i, subset_size=subset_size):
            equilibrate_timestep = i
            LOGGER.info('Model Equilibrated at Timestep %i', equilibrate_timestep)
        # Find Numbers for Next Population
        N_next, Spawners_t[i+1] = cycle_func(N_tasx[i])
        N_tasx[i+1] = N_next

    # Run Harvest and Check Equilibrium for Final Population
    if harvest_func:
        H_x, V_x = harvest_func(N_tasx[-1])
        H_tx[-1] = H_x
        V_tx[-1] = V_x
    if not equilibrate_timestep and len(N_tasx) >= subset_size and _is_equilibrated(H_tx, len(N_tasx)-1, subset_size=subset_size):
        equilibrate_timestep = len(N_tasx)
        LOGGER.info('Model Equilibrated at Timestep %i', equilibrate_timestep)

    # Store Results in Variables Dictionary
    vars_dict['N_tasx'] = N_tasx
    vars_dict['H_tx'] = H_tx
    vars_dict['V_tx'] = V_tx
    vars_dict['Spawners_t'] = Spawners_t
    vars_dict['equilibrate_timestep'] = equilibrate_timestep

    return vars_dict


# Helper functions for run_population_model
def _calc_moving_average(H):
    mov_avg = H.sum() / len(H)
    return mov_avg


def _is_equilibrated(H_tx, i, tolerance=0.001, subset_size=10):
    mov_avg = _calc_moving_average(H_tx[i-(subset_size-1): i+1])
    cur = H_tx[i].sum()
    frac = mov_avg / cur
    diff = np.abs(frac - 1)

    if diff < tolerance:
        return True
    else:
        return False

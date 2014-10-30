import logging

import numpy as np

LOGGER = logging.getLogger('FISHERIES')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

'''
**Notes**

Notation:
x, r: area/region
a, c: age/class
s: sex
t: time

    Example: N_asx (Three-dimensional Numbers matrix)
        first index: class
        last index (first degree): region

Presumed Order of Axes for Given Functions:

    Recruitment
        N:              region, sex, class
        Class Vectors:  (None), sex, class

    Initial Conditions
        N:  class, sex, region
        S:  class, sex, region

    Cycle
        N:  class, sex, region
        S:  class, sex, region
'''


def initialize_vars(vars_dict):
    '''Initializes variables

    **Example Output**
    vars_dict = {
        # (other items)
        ...
        'Survtotalfrac': np.array([...]),  # Index Order: class, sex, region
        'G_survtotalfrac': np.array([...]),  # (same)
        'P_survtotalfrac': np.array([...]),  # (same)
        'N_tasx': np.array([...]),  # Index Order: time, class, sex, region
        'H_tx': np.array([...]), # Time, Region
        'V_tx': np.array([...]), # Time, Region
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


def set_recru_func(vars_dict):
    '''
    Creates recruitment function that calculates the number of recruits for
        class 0 at time t for each region (currently sex agnostic). Also
        returns number of spawners

    Returns single array region-element vectors for recruitment class
        work will have to be done outside the function to massage the
        array into N_prev

    **Example Output of Returned Recruitment Function**
    np.array([1.5, 2.2, 3.6, 4.9])  # Recruitment in each region
    45  # Number of Spawners

    N_next[0], spawners = rec_func(N_prev)
    '''
    def create_Spawners(Matu, Weight):
        return lambda N_prev: (N_prev * Matu * Weight).sum()

    def create_BH(alpha, beta, sexsp, Matu, Weight, LarvDisp):
        spawners = create_Spawners(Matu, Weight)
        return lambda N_prev: (LarvDisp * ((alpha * spawners(
            N_prev) / (beta + spawners(N_prev)))) / sexsp, spawners(N_prev))

    def create_Ricker(alpha, beta, sexsp, Matu, Weight, LarvDisp):
        spawners = create_Spawners(Matu, Weight)
        return lambda N_prev: (LarvDisp * (alpha * spawners(N_prev) * (
            np.e ** (-beta * spawners(N_prev)))) / sexsp, spawners(N_prev))

    def create_Fecundity(Fec, sexsp, Matu, LarvDisp):
        spawners = create_Spawners(Matu, Fec)
        return lambda N_prev: (LarvDisp * spawners(
            N_prev) / sexsp, spawners(N_prev))

    def create_Fixed(fixed, sexsp, LarvDisp):
        return lambda N_prev: (LarvDisp * fixed / sexsp, None)

    sexsp = vars_dict['sexsp']
    LarvDisp = vars_dict['Larvaldispersal']

    # Initialize Weight vector according to spawn_units
    if vars_dict['spawn_units'] == "Weight":
        Weight = vars_dict['Weight']
    else:
        Weight = np.ones([sexsp, len(vars_dict['Classes'])])

    # Create Recruitment Function
    if vars_dict['recruitment_type'] == "Beverton-Holt":
        alpha = vars_dict['alpha']
        beta = vars_dict['beta']
        Matu = vars_dict['Maturity']
        return create_BH(alpha, beta, sexsp, Matu, Weight, LarvDisp)
    elif vars_dict['recruitment_type'] == "Ricker":
        alpha = vars_dict['alpha']
        beta = vars_dict['beta']
        Matu = vars_dict['Maturity']
        return create_Ricker(alpha, beta, sexsp, Matu, Weight, LarvDisp)
    elif vars_dict['recruitment_type'] == "Fecundity":
        Fec = vars_dict['Fecundity']
        Matu = vars_dict['Maturity']
        return create_Fecundity(Fec, sexsp, Matu, LarvDisp)
    elif vars_dict['recruitment_type'] == "Fixed":
        fixed = vars_dict['total_recur_recruits']
        return create_Fixed(fixed, sexsp, LarvDisp)
    else:
        LOGGER.error("Could not determine correct recruitment function")
        raise ValueError


def set_init_cond_func(vars_dict):
    '''
    Creates a function to set the initial conditions of the model

    **Example Output of Returned Initial Condition Function**
    N_asx = np.ndarray([...])
    '''
    S = vars_dict['Survtotalfrac']  # S_asx
    sexsp = vars_dict['sexsp']
    total_init_recruits = vars_dict['total_init_recruits']
    num_regions = len(vars_dict['Regions'])
    num_classes = len(vars_dict['Classes'])

    def age_based_init_cond():
        '''
        Returns N_0_asx
        '''

        N_0 = np.zeros([num_classes, sexsp, num_regions])

        N_0[0] = total_init_recruits / (sexsp * num_regions)

        for i in range(1, num_classes-1):
            N_0[i] = N_0[i-1] * S[i-1]

        if len(N_0) > 1:
            N_0[-1] = (N_0[-2] * S[-2]) / (1 - S[-1])

        return N_0

    def stage_based_init_cond():
        '''
        Returns N_0_asx
        '''
        N_0 = np.zeros([num_classes, sexsp, num_regions])

        N_0[0] = total_init_recruits / (sexsp * num_regions)
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

    **Example Output of Returned Cycle Function**
    N_asx = np.ndarray([...])
    spawners = <int>

    N_next, spawners = cycle_func(N_prev)
    '''
    S = vars_dict['Survtotalfrac']  # S_asx
    P = vars_dict['P_survtotalfrac']  # P_asx
    G = vars_dict['G_survtotalfrac']  # G_asx
    num_classes = len(vars_dict['Classes'])
    Migration = vars_dict['Migration']

    def age_based_cycle_func(N_prev):
        '''Return next cycle numbers and number of spawners used in recruitment
        during that cycle

        N_asx, spawners
        '''
        N_next = np.ndarray(N_prev.shape)

        N_prev_xsa = N_prev.swapaxes(0, 2)
        N_next_0_xsa, spawners = rec_func(N_prev_xsa)
        N_next[0] = N_next_0_xsa.swapaxes(0, 2)

        for i in range(1, num_classes):
            N_next[i] = np.array(map(lambda x: Migration[i-1].dot(x), N_prev[i-1]))[:, 0, :] * S[i-1]

        if len(N_prev) > 1:
            N_next[-1] = N_next[-1] + np.array(map(lambda x: Migration[-1].dot(x), N_prev[-1]))[:, 0, :] * S[-1]

        return N_next, spawners

    def stage_based_cycle_func(N_prev):
        '''Return next cycle numbers and number of spawners used in recruitment
        during that cycle

        N_asx, spawners
        '''
        N_next = np.ndarray(N_prev.shape)

        N_prev_xsa = N_prev.swapaxes(0, 2)
        N_next_0_xsa, spawners = rec_func(N_prev_xsa)
        N_next[0] = N_next_0_xsa.swapaxes(0, 2)

        N_next[0] = N_next[0] + np.array(map(
            lambda x: Migration[0].dot(x), N_prev[0])) * S[0]

        for i in range(1, num_classes):
            G_comp = np.array(map(lambda x: Migration[i-1].dot(x), N_prev[i-1]))[:, 0, :] * G[i-1]
            P_comp = np.array(map(lambda x: Migration[i].dot(x), N_prev[i]))[:, 0, :] * P[i]
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
        of the fisheries population over each timestep for a given region.
        Returns None if harvest isn't selected by user.

    **Example Outputs of Returned Harvest Function**
    H_x, V_x = harv_func(N_tasx)

    H_x = np.array([3.0, 4.5, 2.5, ...])
    V_x = np.array([6.0, 9.0, 5.0, ...])

    '''
    if True:  # vars_dict['harv_cont']:

        sexsp = vars_dict['sexsp']
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
            N_xsa = N_asx.swapaxes(0, 2)
            H_xsa = N_xsa * I * Weight
            H_x = np.array(map(lambda x: x.sum(), H_xsa))
            V_x = H_x * (frac_post_process * unit_price)
            return H_x, V_x

        return harv_func

    else:
        return None


def run_population_model(vars_dict, init_cond_func, cycle_func, harvest_func):
    '''Run model

    **Example Output**
    vars_dict = {
        # (other items)
        ...
        'N_tasx': np.array([...]),  # Index Order: time, class, sex, region
        'H_tx': np.array([...]),  # Index Order: time, region
        'V_tx': np.array([...]),  # Index Order: time, region
        'Spawners_t': np,array([...]),
        'equilibrate_cycle': <int>,
    }
    '''
    N_tasx = vars_dict['N_tasx']
    H_tx = vars_dict['H_tx']
    V_tx = vars_dict['V_tx']
    Spawners_t = vars_dict['Spawners_t']
    equilibrate_cycle = False
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
        if not equilibrate_cycle and i >= subset_size and _is_equilibrated(H_tx, i, subset_size=subset_size):
            equilibrate_cycle = i
            LOGGER.info('Model Equilibrated at Cycle %i', equilibrate_cycle)
        # Find Numbers for Next Population
        N_next, Spawners_t[i+1] = cycle_func(N_tasx[i])
        N_tasx[i+1] = N_next

    # Run Harvest and Check Equilibrium for Final Population
    if harvest_func:
        H_x, V_x = harvest_func(N_tasx[-1])
        H_tx[-1] = H_x
        V_tx[-1] = V_x
    if not equilibrate_cycle and len(N_tasx) >= subset_size and _is_equilibrated(H_tx, len(N_tasx)-1, subset_size=subset_size):
        equilibrate_cycle = len(N_tasx)
        LOGGER.info('Model Equilibrated at Cycle %i', equilibrate_cycle)

    # Store Results in Variables Dictionary
    vars_dict['N_tasx'] = N_tasx
    vars_dict['H_tx'] = H_tx
    vars_dict['V_tx'] = V_tx
    vars_dict['Spawners_t'] = Spawners_t
    vars_dict['equilibrate_cycle'] = equilibrate_cycle

    return vars_dict


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

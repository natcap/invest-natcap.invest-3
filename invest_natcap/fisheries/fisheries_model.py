import logging

import numpy as np

LOGGER = logging.getLogger('FISHERIES')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

'''
Notes

Presumed Order or Axes for Given Functions:

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
    Creates recruitment function that calculates the number of recruits for
        class 0 at time t for each region (currently sex agnostic)

    Returns single array region-element vectors for recruitment class
        work will have to be done outside the function to massage the
        array into N_prev

    **Example Output of Returned Recruitment Function**
    np.array([1.5, 2.2, 3.6, 4.9])  # Recruitment in each region

    '''
    def create_Spawners(Matu, Weight):
        return lambda N_prev: (N_prev * Matu * Weight).sum()

    def create_BH(alpha, beta, sexsp, Matu, Weight, LarvDisp):
        spawners = create_Spawners(Matu, Weight)
        return lambda N_prev: LarvDisp * ((alpha * spawners(
            N_prev) / (beta + spawners(N_prev)))) / sexsp

    def create_Ricker(alpha, beta, sexsp, Matu, Weight, LarvDisp):
        spawners = create_Spawners(Matu, Weight)
        return lambda N_prev: LarvDisp * (alpha * spawners(
            N_prev) * (np.e ** (-beta * spawners(N_prev)))) / sexsp

    def create_Fecundity(Fec, sexsp, Matu, LarvDisp):
        spawners = create_Spawners(Matu, Fec)
        return lambda N_prev: LarvDisp * spawners(N_prev) / sexsp

    def create_Fixed(fixed, sexsp, LarvDisp):
        return lambda N_prev: LarvDisp * fixed / sexsp

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


def set_harvest_func(vars_dict):
    '''
    Creates harvest function that calculates the given harvest and valuation
        of the fisheries population over each timestep. Returns None if harvest
        isn't selected by user

    **Example Outputs of Returned Harvest Function**
    H_tx, V_tx = harv_func(N_all)

    H_tx = np.array([3.0, 4.5, 2.5, ...])  # AWAITING RESPONSE FROM LAUREN
    V_tx = np.array([6.0, 9.0, 5.0 ...])   # AWAITING RESPONSE FROM LAUREN

    '''
    if vars_dict['harv_cont']:

        sexsp = vars_dict['sexsp']
        frac_post_process = vars_dict['frac_post_process']
        unit_price = vars_dict['unit_price']

        # Initialize Weight vector according to spawn_units
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

        def harv_func(N_all):
            H = N_all * I * Weight
            H = np.array(map(lambda x: x.sum(), H[:]))
            V = H * (frac_post_process * unit_price)
            return H, V

        return harv_func

    else:
        return None


def set_init_cond_func(vars_dict, rec_func):
    '''
    Creates a function to set the initial conditions of the model

    **Example Output of Returned Harvest Function**
    N_xsa = np.array([...])
    '''
    ##### AXES CURRENTLY OUT OF ORDER
    S = vars_dict['Survtotalfrac']

    def age_based_init_cond(vars_dict):
        '''
        Returns N_0_csr
        '''
        N_0 = np.zeros([len(vars_dict['Classes']), len(
            vars_dict['sexsp']), len(vars_dict['Regions'])])

        for i in range(1, len(vars_dict['Classes']) - 1):
            N_0[i] = N_0[i - 1] * S
            pass

        N_0[-1] = (N_0[-1] * S) / (1 - S)

        N_0[0] = rec_func(
            N_0.swapaxes(0, 2)).swapaxes(0, 2)   # NOT RIGHT: NEEDS TO TAKE SEXSP INTO ACCOUNT

        return N_0

    def stage_based_init_cond(vars_dict):
        '''
        Returns N_0_csr
        '''
        N_0 = np.zeros([len(vars_dict['Classes']), len(
            vars_dict['sexsp']), len(vars_dict['Regions'])])

        N_0[1:] = 1
        N_0[0] = rec_func(N_0.swapaxes(0, 2)).swapaxes(0, 2)  # NOT RIGHT: NEEDS TO TAKE SEXSP INTO ACCOUNT

        return N_0

    if vars_dict['Age-Based'] == 'Age-Based':
        return age_based_init_cond

    elif vars_dict['Stage-Based'] == 'Stage-Based':
        return stage_based_init_cond

    else:
        LOGGER.error("Could not determine which initial_condition function to use")


def set_cycle_func(vars_dict, rec_func, harvest_func):
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

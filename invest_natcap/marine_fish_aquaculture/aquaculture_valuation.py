'''Invest finfish aquaculture filehandler for valuation'''


def exectute(args):
    
    """This function will take care of preparing files passed into 
    the finfish aquaculture model. It will handle all files/inputs associated
    with valuation calculations and manipulations. It will create objects
    to be passed to the aquaculture_core.py module. It may write log, 
    warning, or error messages to stdout.
    
    args: a python dictionary containing the following data:
    args['names']: Numeric text string (positive int or float)
    args['f_type']:text string
    args['p_per_kg']: MArket price per kilogram of processed fish
    args['frac_p']: Fraction of market price that accounts for costs rather than
                    profit
    args['discount']: Daily market discount rate
    """
    
    #Initialize new dictionary that will store only valuation data, pass data in

    #No, but seriously, is there anything else?
    
    valuation_args = {}
    
    valuation_args['names'] = args['names']
    valuation_args['f_type'] = args['f_type']
    valuation_args['p_per_kg'] = args['p_per_kg']
    valuation_args['frac_p'] = args['frac_p']
    valuation_args['discount'] = args['discount']

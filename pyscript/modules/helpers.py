def is_float(string):
    """ 
    Will try to cast an string to float, and fallsback to zero if not 
    This should suffice for both casting and boolean operations.
    """
    try:
        return float(string)
    except ValueError:
        return 0
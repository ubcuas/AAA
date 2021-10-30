import utm

def f_2_m(feet_val):
    """
    SHORTHAND
    [param] feet_val - Input (number) value in feet
    [return] A value converted to meters (float)
    """
    return feet_to_meter(feet_val)

def feet_to_meter(feet_val):
    """
    [param] feet_val - Input (number) value in feet
    [return] A value converted to meters (float)
    """
    return feet_val * 0.3048

def m_2_f(meter_val):
    """
    SHORTHAND
    [param] metre_val - Input (number) value in meters
    [return] A value converted to feet (float)
    """
    return meter_to_feet(meter_val)

def meter_to_feet(meter_val):
    """
    [param] metre_val - Input (number) value in meters
    [return] A value converted to feet (float)
    """
    return meter_val / 0.3048

utm_meta = None
def ll_to_utm(longitude, latitude):
    """
    Converts a longitude and latitude pair into a it's utm coordinate
    """
    global utm_meta
    utm_meta = utm.from_latlon(latitude, longitude)[2:]
    return utm.from_latlon(latitude, longitude)[:2]

def utm_to_ll(x, y):
    """
    Converts a utm coordinate to latitude and longitude
    """
    global utm_meta
    return reversed(utm.to_latlon(x, y, *utm_meta))

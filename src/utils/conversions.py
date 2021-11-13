import utm

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

'''
import logging
import asyncio

from gcomx.settings.local import MEDIA_ROOT
from interop.client import Client

logger = logging.getLogger(__name__)

THUMBNAIL_DIR = MEDIA_ROOT + "/objects/"
odlc_cache = []

def convert_odlc_to_json(odlc):
    from interop.views import current_mission_id

    json_odlc = {
                    'id': odlc.auvsi_id,
                    'mission': current_mission_id,
                    'type': odlc.type.upper(),
                    'latitude': float(odlc.latitude),
                    'longitude': float(odlc.longitude),
                    'orientation': odlc.orientation.upper(),
                    'shape': odlc.shape.upper(),
                    'shapeColor': odlc.background_color.upper(),
                    'alphanumeric': odlc.alphanumeric.upper(),
                    'alphanumericColor': odlc.alphanumeric_color.upper(),
                    'description': odlc.description,
                    'autonomous': False,
                }

    # Strip out empty fields:
    for key, val in json_odlc.items():
        if val == "":
            json_odlc[key] = None

    return json_odlc

def update_odlc_cache():
    global odlc_cache
    gcom_client = Client()

    odlc_cache = gcom_client.get_odlcs()
    logger.debug("ODLC cache updated")

def post_or_put_odlc(sender, **kwargs):
    global odlc_cache
    gcom_client = Client()

    # Update cache
    update_odlc_cache()

    # Get model
    odlc = kwargs['instance']
    logger.debug("Sending %s to interop-server" % odlc.name)

    # Convert to AUVSI model
    json_odlc = convert_odlc_to_json(odlc)
    logger.debug("ODLC as JSON is: %s" % json_odlc)

    # Check if inside cache
    exists = False
    for cached_odlc in odlc_cache:
        # logger.debug("ODLC cache_check {} - {}".format(json_odlc['id'], item['id']))
        if json_odlc['id'] == cached_odlc['id']:
            exists = True
            logger.info("ODLC cache hit!")

            # If nothing has changed, exit function
            differ = False
            for key, value in json_odlc.items():
                if key not in cached_odlc:
                    differ = True
                elif cached_odlc[key] != value:
                    differ = True
            if not differ:
                logger.debug("No ODLC changes to update")
                return

            break  # Otherwise break from cache loop

    # POST or PUT to interop-servers
    if not exists:
        logger.debug("ODLC not found in cache... posting")
        result = gcom_client.post_odlc(json_odlc)
    else:
        logger.debug("ODLC found in cache... putting")
        result = gcom_client.put_odlc(json_odlc)

    # Update the ID value returned
    logger.debug("Got %s as the full ODLC object", result)
    if result:
        odlc.auvsi_id = result['id']

async def post_odlc_thumbnail(odlc):
    gcom_client = Client()

    # Convert to AUVSI model
    logger.debug("Sending %s thumbnail to interop-server" % odlc.name)
    json_odlc = convert_odlc_to_json(odlc)

    print(json_odlc)

    # POST the thumbnail image to the interop server
    logger.debug("POSTing ODLC %s thumbnail", odlc.auvsi_id)
    thumb_fn = THUMBNAIL_DIR + "%s.jpg"%odlc.id
    gcom_client.post_odlc_image(json_odlc, thumb_fn)

def delete_odlc(sender, **kwargs):
    global odlc_cache
    gcom_client = Client()

    # Get model
    odlc = kwargs['instance']
    logger.debug("Deleting %s from interop-server" % odlc.name)

    result = gcom_client.delete_odlc(odlc.auvsi_id)

    # Update cache
    update_odlc_cache()
'''
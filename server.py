import os
import logging

from main import app
from gevent.pywsgi import WSGIServer

if __name__ == "__main__":
    # set logging
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if os.environ['TRV_DEBUG'] == 'True':
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    http_server.serve_forever()

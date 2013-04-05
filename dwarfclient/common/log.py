#!/usr/bin/python

import logging
import os

from dwarfclient.common import config

CONF = config.CONF


def init(args):
    """
    Initialize the logger
    """
    if not os.path.exists(CONF.dwarf_dir):
        return

    # Create the logger
    logger = logging.getLogger('dwarf')
    logger.setLevel(logging.DEBUG)

    # Create file handler which logs everything
    fh = logging.FileHandler(CONF.dwarf_log)
    fh.setLevel(logging.DEBUG)

    # Create a formatter and add it to the handler
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(fh)

    if args.verbose:
        # log to the console
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        logger.addHandler(ch)


LOG = logging.getLogger('dwarf')

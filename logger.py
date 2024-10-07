import logging


# Configure the logger
def setup_logger():
    # Create a custom logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Set the logging level to DEBUG

    # Create a console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)  # Set the console handler level to DEBUG

    # Create a custom formatter
    formatter = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    # Set the formatter for the console handler
    ch.setFormatter(formatter)

    # Add the console handler to the logger
    logger.addHandler(ch)

    return logger


logger = setup_logger()


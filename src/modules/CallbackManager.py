import os
import inspect
import json
import logging

def register_callback_ue(callback_function, event_type):
    """
    Registers a callback function for the specified event type and stores it in a file called callbacks.py.

    This function takes a callback function and an event type as input parameters. It extracts the source code
    of the callback function and writes it to a file called callbacks.py. Additionally, it updates an events.json
    file to store the registered callback function under the corresponding event type.

    :param callback_function: The callback function to register.
    :type callback_function: function
    :param event_type: The type of event for which the callback function is registered (e.g., "RegisteredUEs", "UEStatus").
    :type event_type: str
    :return: None
    :raises: Exception if an error occurs while writing to the file.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    home_directory = os.path.expanduser("~")
    callbacks_path = os.path.join(home_directory, '5gcsdk', 'src', 'modules' , 'callbacks.py')
    events_json_path = os.path.join(home_directory, '5gcsdk', 'src' , 'modules' , 'events.json')
    function_source = inspect.getsource(callback_function)

    try:
        with open(callbacks_path, 'a') as file:
            file.write(function_source)
            file.write("\n\n")
            logger.info("Callback function registered successfully.")
    except Exception as e:
        logger.error(f"An error occurred while writing to the file: {e}")
        raise
    else:
        file.close()
        logger.info("File saved and closed.")

    with open(events_json_path, 'r') as json_file:
        data = json.load(json_file)

    function_name = callback_function.__name__

    if event_type == "RegisteredUEs":
        data["events"]["RegisteredUEs"]["callbacks"].append(function_name)
    elif event_type == "UEStatus":
        data["events"]["UEStatus"]["callbacks"].append(function_name)
    elif event_type == "UECellID":
        data["events"]["UECellID"]["callbacks"].append(function_name)
    elif event_type == "UETraffic":
        data["events"]["UETraffic"]["callbacks"].append(function_name)

    with open(events_json_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)



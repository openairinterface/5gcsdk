import os
import inspect
import json
import logging
import re
from enum import Enum
import ast
class EventType(Enum):
    REGISTERED_UES = "RegisteredUEs"
    UE_STATUS = "UEStatus"
    UE_CELL_ID = "UECellID"
    UE_TRAFFIC = "UETraffic"

def register_callback_ue(callback_function, event_type):
    """
    Registers a callback function for the specified event type and stores it in a file called callbacks.py.

    This function takes a callback function and an event type as input parameters. It extracts the source code
    of the callback function and writes it to a file called callbacks.py. Additionally, it updates an events.json
    file to store the registered callback function under the corresponding event type.

    :param callback_function: The callback function to register.
    :type callback_function: function
    :param event_type: The type of event for which the callback function is registered (e.g., EventType.REGISTERED_UES).
    :type event_type: EventType
    :return: None
    :raises: Exception if an error occurs while writing to the file.

    Usage Example:
    --------------
    >>> def sample_callback(data):
    >>>     print("Callback called with data:", data)
    >>> 
    >>> register_callback_ue(sample_callback, EventType.REGISTERED_UES)
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    callbacks_path = os.path.join(parent_dir, 'modules', 'callbacks.py')
    events_json_path = os.path.join(parent_dir, 'modules', 'events.json')
    
    assert isinstance(event_type, EventType), "Invalid event type"
    
    function_name = callback_function.__name__
    event_type_str = event_type.value

    try:
        with open(events_json_path, 'r') as json_file:
            data = json.load(json_file)

        assert "events" in data, "events key not found in events.json"
        assert event_type_str in data["events"], f"{event_type_str} not found in events.json"
        assert "callbacks" in data["events"][event_type_str], "callbacks key not found in the event type in events.json"

        # Check if the callback function is already registered for the event type
        if function_name in data["events"][event_type_str]["callbacks"]:
            raise ValueError(f"Callback function '{function_name}' is already registered for event type '{event_type_str}'.")

        # Add the function to the events.json data
        data["events"][event_type_str]["callbacks"].append(function_name)

        with open(events_json_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        logger.info(f"Callback function registered successfully for event type: {event_type_str}")

        # If the function name is not already registered, write the function to callbacks.py
        try:
            function_source = inspect.getsource(callback_function)
            with open(callbacks_path, 'a') as file:
                file.write(function_source)
                file.write("\n\n")
            logger.info("Callback function source written to callbacks.py successfully.")
        except Exception as e:
            # If writing to callbacks.py fails, rollback the change in events.json
            data["events"][event_type_str]["callbacks"].remove(function_name)
            with open(events_json_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)
            logger.error(f"An error occurred while writing to callbacks.py: {e}")
            raise

    except AssertionError as error:
        logger.error(f"Assertion error: {error}")
        raise
    except ValueError as error:
        logger.error(f"Value error: {error}")
        raise
    except Exception as e:
        logger.error(f"An error occurred while updating events.json: {e}")
        raise



def unregister_callback_ue(function_name=None, event_type=None):
    """
    Unregisters a callback function for the specified event type and removes it from callbacks.py and events.json.
    If no arguments are provided, removes all callback functions from callbacks.py and events.json.

    :param function_name: The name of the callback function to unregister.
    :type function_name: str, optional
    :param event_type: The type of event for which the callback function is unregistered (e.g., EventType.REGISTERED_UES).
    :type event_type: EventType, optional
    :return: None
    :raises: Exception if an error occurs while modifying the files.

    Usage Example:
    --------------

    >>> event = EventType.REGISTERED_UES
    >>> unregister_callback_ue('sample_callback', event)
    >>> unregister_callback_ue()  # This will remove all callback functions
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    filepath = os.path.join(parent_dir, 'modules', 'callbacks.py')
    events_json_path = os.path.join(parent_dir, 'modules', 'events.json')
    
    if function_name is None and event_type is None:
        # Remove all callback functions from callbacks.py
        try:
            with open(filepath, 'w') as f:
                f.write("")  # Empty the file
            logger.info("All callback functions removed from callbacks.py successfully.")
        except Exception as e:
            logger.error(f"An error occurred while modifying callbacks.py: {e}")
            raise

        # Update events.json to remove all callback function references
        try:
            with open(events_json_path, 'r') as json_file:
                data = json.load(json_file)

            assert "events" in data, "events key not found in events.json"
            for event in data["events"]:
                data["events"][event]["callbacks"] = []

            with open(events_json_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)

            logger.info("All callback functions removed from events.json successfully.")
        except AssertionError as error:
            logger.error(f"Assertion error: {error}")
            raise
        except Exception as e:
            logger.error(f"An error occurred while updating events.json: {e}")
            raise
    else:
        assert isinstance(function_name, str), "Function name must be a string"
        assert isinstance(event_type, EventType), "Invalid event type"
        
        # Remove the function definition from callbacks.py
        try:
            with open(filepath, 'r') as f:
                source_code = f.read()

            tree = ast.parse(source_code)

            class FunctionRemover(ast.NodeTransformer):
                def visit_FunctionDef(self, node):
                    if node.name == function_name:
                        return None  # Remove the function definition
                    return node

            remover = FunctionRemover()
            modified_tree = remover.visit(tree)
            modified_source_code = ast.unparse(modified_tree)

            with open(filepath, 'w') as f:
                f.write(modified_source_code)
            
            logger.info(f"Callback function {function_name} removed from callbacks.py successfully.")
        except Exception as e:
            logger.error(f"An error occurred while modifying callbacks.py: {e}")
            raise

        # Update events.json to remove the callback function reference
        try:
            with open(events_json_path, 'r') as json_file:
                data = json.load(json_file)

            event_type_str = event_type.value

            assert "events" in data, "events key not found in events.json"
            assert event_type_str in data["events"], f"{event_type_str} not found in events.json"
            assert "callbacks" in data["events"][event_type_str], "callbacks key not found in the event type in events.json"

            callbacks_list = data["events"][event_type_str]["callbacks"]
            
            if function_name in callbacks_list:
                callbacks_list.remove(function_name)
            else:
                logger.warning(f"Callback function {function_name} not found in events.json for event type: {event_type_str}")

            with open(events_json_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)

            logger.info(f"Callback function {function_name} unregistered successfully for event type: {event_type_str}")
        except AssertionError as error:
            logger.error(f"Assertion error: {error}")
            raise
        except Exception as e:
            logger.error(f"An error occurred while updating events.json: {e}")
            raise
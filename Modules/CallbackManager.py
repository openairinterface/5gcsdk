import inspect
import json

def registerCallbackUE(callback_function , event_type):
    """
    Registers a callback function for UE and stores it in a file called callbacks.py.
    """
    function_source = inspect.getsource(callback_function)
    
    try:
        with open('/home/achraf/oai_cn_sdk/Modules/callbacks.py', 'a') as file:
            file.write("\n\n")
            file.write(function_source)
            print("Callback function registered successfully.")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")
    else:
        file.close()
        print("File saved and closed.")
    with open('/home/achraf/oai_cn_sdk/Modules/events.json', 'r') as json_file:
        data = json.load(json_file)
    
    function_name = callback_function.__name__

    if event_type == "RegisteredUEs":
        data["events"]["RegisteredUEs"]["callbacks"].append(function_name)    
    if event_type == "UEStatus":
        data["events"]["UEStatus"]["callbacks"].append(function_name)
    if event_type == "UECellID":
        data["events"]["UECellID"]["callbacks"].append(function_name)
    if event_type == "UETraffic":
        data["events"]["UETraffic"]["callbacks"].append(function_name)
    
    with open('/home/achraf/oai_cn_sdk/Modules/events.json', 'w') as json_file:
      json.dump(data, json_file, indent=4)


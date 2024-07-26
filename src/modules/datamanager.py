from data_models.DataStream import DataStream


def createDataStream(data_selection = [], filters = None, callback = None):
    """
    Create a new data stream
    
    Parameters:
    data_selection (list): List of metrics to be selected
    filters (list): List of filters to be applied to the data stream: [(metric, operator, value), ...]
    callback (function): Callback function to be called when data is received

    Returns:
    DataStream: DataStream object
    """
    data_stream = DataStream(data_selection=data_selection, filters=filters, callback=callback)

    return data_stream


def saveDataStream(dataStream = None, ues_history = []):
    """
    Save data stream to csv file

    Parameters:
    dataStream (DataStream): DataStream object
    ues_history (list): List of UEs history

    Returns:
    None
    """
    if dataStream and isinstance(dataStream, DataStream):
        dataStream.save(ues_history)
    else:
        print('Not a DataStream object')

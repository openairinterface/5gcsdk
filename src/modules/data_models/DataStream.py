import csv
import operator


class DataStream:
    def __init__(self, data_selection = [], filters = None, callback = None):
        """
        Initialize the DataStream object.

        :param data_selection: List of Metric enums representing the selected metrics to be included in the output.
        :param filters: Array of filters to be applied to the data stream: [(metric, operator, value), ...]
        :param callback: Function to be called back when a data stream is processed.
        """
        self.data_selection = data_selection
        self.filters = filters
        self.callback = callback

    def apply_filters(self, ue):
        """
        Apply the filters to a UE.

        :param ue: Dictionary representing the data of a UE (User Equipment).
        :return: Boolean indicating whether the UE passes all filters.
        """
        operators = {
            '==': operator.eq,
            '!=': operator.ne,
            '>': operator.gt,
            '<': operator.lt,
            '>=': operator.ge,
            '<=': operator.le
        }

        for metric, op, value in self.filters:
            if metric.name == 'plmn': # Special handling for 'plmn' metric
                plmn_mcc = ue['plmn_mcc']
                plmn_mnc = ue['plmn_mnc']
                if not (operators[op](plmn_mcc, value) or operators[op](plmn_mnc, value)):
                    return False
            else:
                if not operators[op](ue[metric.name], value):
                    return False
        return True

    def save(self, ues = []):
        """
        Save the data to a CSV file.

        :param ues: List of dictionaries, each representing the data of a UE (User Equipment).

        :return: None
        """
        # Prepare the fieldnames for the CSV file based on the selected metrics 
        fieldnames = []
        for metric in self.data_selection:
            if metric.name == 'plmn': # 'plmn' is a composite metric with 'mcc' and 'mnc', so add both fields
                fieldnames.append('plmn_mcc')
                fieldnames.append('plmn_mnc')
            else:
                # Add the metric name as a fieldname
                fieldnames.append(metric.name)

        # Open the CSV file for writing
        with open('dataStream.csv', mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()

            for ue in ues:
                if self.apply_filters(ue):
                    # Filter the UE data to include only the selected metrics
                    filtered_ue = {key: ue[key] for key in fieldnames}
                    writer.writerow(filtered_ue)
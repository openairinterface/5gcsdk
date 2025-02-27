import sys
import os 
from datetime import datetime
current_dir = os.path.dirname(os.path.abspath(__file__))
src_main_dir = os.path.join(current_dir, '../src/main')
sys.path.append(src_main_dir)

#==========================================import sdk===========================================================================

import oai5gc


#==========================================add one ue ==========================================================================

#oai5gc.RFsimUEManager.add_ues(1)

#========================================== list connected ues containers =======================================================

#oai5gc.RFsimUEManager.list_connected_ues()

#==========================================give registred ues =================================================================

#print(oai5gc.UEManager.get_registered_ues())

#==========================================add 2 ues ===========================================================================

#print(oai5gc.UEManager.get_ue_location('imsi-208990000000031'))

#print(oai5gc.UEManager.get_ue_status('12.1.1.130'))


#==========================================get anomaly ratio===================================================================

#print(oai5gc.get_anomaly_ratio())

#==========================================remove one ue =======================================================================

#oai5gc.RFsimUEManager.remove_ues(1)

#==========================================register traffic callback ============================================================

#def changed_statue_ue(ue):
#   print("this ue has changed its statue", ue)

#t=oai5gc.EventType.UEStatus

#oai5gc.register_callback_ue(changed_statue_ue, t)

#==========================================add 2 ues ===========================================================================

#oai5gc.RFsimUEManager.add_ues(1)

#==========================================create data stream  =================================================================

#data_selection = [oai5gc.Metric.imsi, oai5gc.Metric.ip_address]

#filters = [('registration_status', '==', 'REGISTERED')]

#ds=oai5gc.create_data_stream(data_selection , filters )

#==========================================save data stream ============================================================

#oai5gc.save_data_to_csv(ds , 'datastream.csv')

#==========================================srun traffic server  ============================================================

#DEFAULT_DISTRIBUTION_TYPE = 'gaussian'  # Use 'gaussian' as default
#DEFAULT_TOTAL_DURATION = 60  #  total duration in seconds
#DEFAULT_MEAN_INTERVAL = 5  #  mean interval in seconds
#DEFAULT_STDDEV_INTERVAL = 1  #  standard deviation for intervals
#DEFAULT_TOTAL_BANDWIDTH = 1000  #  total bandwidth in Mbps
#DEFAULT_MEAN_BANDWIDTH = 200  #  mean bandwidth per interval in Mbps
#DEFAULT_STDDEV_BANDWIDTH = 50  #  standard deviation for bandwidth
#on_off                   = 20   # % of the OFF time 
#oai5gc.UEManager.run_iperf_random("192.168.70.160" , "gaussian" , 60 , 5 , 3 , 1000 , 200 , 50 , 20)
#oai5gc.UEManager.random_iperf_logs()
#==========================================stop handler  ============================================================

oai5gc.stop_handler()


import sys
import os 

current_dir = os.path.dirname(os.path.abspath(__file__))
src_main_dir = os.path.join(current_dir, '../src/main')
sys.path.append(src_main_dir)

import oai5gc

#oai5gc.stop_handler()


#oai5gc.add_ues(1)

#print(oai5gc.get_registered_ues())

#oai5gc.remove_ues(3)

#oai5gc.get_ue_status('12.1.1.2')
#12.1.1.2
def sample_callback(data):
    imsi = list(data.keys())[0]
    print("New UE is registred with imsi:", imsi)


#def sample_callback2(data):
  #   imsi = list(data.keys())[0]
 #    print("A UE status is updated with imsi:", imsi)
a=oai5gc.EventType.REGISTERED_UES
#oai5gc.register_callback_ue(sample_callback, a)
#oai5gc.unregister_callback_ue()
#oai5gc.register_callback_ue(sample_callback2, "UEStatus")

#oai5gc.add_ues(2)

oai5gc.remove_ues(4)

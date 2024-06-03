import sys
import os 

current_dir = os.path.dirname(os.path.abspath(__file__))
src_main_dir = os.path.join(current_dir, '../src/main')
sys.path.append(src_main_dir)

import oai5gc

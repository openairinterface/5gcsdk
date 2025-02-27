# import pyyaml module
import yaml
from yaml.loader import SafeLoader

configuration = {}

# Open the file and load the file
with open('mnt/config.yaml') as f:
    data = yaml.load(f, Loader=SafeLoader)
    configuration = data

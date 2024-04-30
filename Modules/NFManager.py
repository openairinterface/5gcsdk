from Modules.subscriptions import *
def registerNF(NF,ip):
    """
    Registers a Network Function (NF) with its corresponding IP address.

    This function updates the configuration file with the IP address of the
    specified NF (AMF or SMF) and creates a subscription with the CN 
    related to the NF.

    :param NF: The type of Network Function (AMF or SMF).
    :type NF: str
    :param ip: The IP address of the Network Function.
    :type ip: str
    :return: A message indicating whether the registration was successful.
    :rtype: str

    Output Explanation:
     
    | Output | Meaning                                                      |
    |--------|--------------------------------------------------------------|
    |   "1"  | Registration was successful.                                 |
    |   "0"  | Error occurred during registration.                          |
    |  "00"  | NF provided is not recognized.                               |
    
    """

    if NF == 'AMF':
        amf_sub = createAmfSubscription(amf_ip=ip)
        if amf_sub=='' :
            print("0")
            exit(1)
        else:

            return print("1")
    elif NF == 'SMF':
        smf_sub = createSmfSubscription(smf_ip=ip)
        if smf_sub=='' :
            print("0")
            exit(1)
        else:
            return print("1")
    else:
        return print("00")
    
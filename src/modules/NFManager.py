from subscription import *
def register_nf(nf,ip):
    """
    Registers a Network Function (NF) with its corresponding IP address.

    This function updates the configuration file with the IP address of the
    specified NF (AMF or SMF) and creates a subscription with the CN 
    related to the NF.

    :param nf: The type of Network Function (AMF or SMF).
    :type nf: str
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

    Usage Example:
    --------------
    >>> result = register_nf('AMF', '192.168.1.1')
    >>> print(result)  # Output: "1" (if successful)

    >>> result = register_nf('SMF', '192.168.1.2')
    >>> print(result)  # Output: "1" (if successful)

    >>> result = register_nf('XYZ', '192.168.1.3')
    >>> print(result)  # Output: "00" (NF not recognized)
    """

    if nf == 'AMF':
        amf_sub = createAmfSubscription(amf_ip=ip)
        assert amf_sub, "Error: Failed to create AMF subscription"
        return "1"
    elif nf == 'SMF':
        smf_sub = createSmfSubscription(smf_ip=ip)
        assert smf_sub, "Error: Failed to create SMF subscription"
        return "1"
    else:
        return "00"
    
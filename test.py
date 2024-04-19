from CN_SDK.northbound import *
print("########################################################################")
print("testing get_registered_UEs()..")
existing_users = get_registered_UEs()

# Print or inspect the result
print(existing_users)

print("########################################################################")
print("testing registerNf()..")

nf= 'AMF'
new_ip_address = '192.168.71.132'  # Example new IP address
registerNF(nf,new_ip_address)

print("########################################################################")
print("testing add_UEs()..")

add_UEs(2)

print("########################################################################")
print("testing rm_UEs()..")

rm_UEs(1)

print("########################################################################")  
print("testing get_ue_status_by_imsi()..")

imsi = 'imsi-208990100001100'
status = get_ue_status_by_imsi(imsi)
print(f"Status of UE with IMSI {imsi}: {status}")

#print("########################################################################")
#print("testing #registerCallBackRegisteredUEs()..")

#registerCallBackRegisteredUEs()

print("########################################################################")
print("testing #registerCallBackUEStatus()..")

registerCallBackUEStatus()
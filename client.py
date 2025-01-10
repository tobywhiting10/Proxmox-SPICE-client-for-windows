import os
import subprocess
import json

server = "10.10.20.2" # The address of the server to connect to
node = "miniboi1" # the nodename of the server

vm = "107" # the vm id to initiate a connexion with

username = "root@pam" # username and password to authenticate to the server must have console permission 
relm = "pam"
password = "DJToby1234!"
APIkey = "null"
# Log Levle: NONE, ERROR, INFO, DEBUG
logLevle = "DEBUG"

def getAUTH(username,password,server):
    # Get Data from Proxmox Auth API and dump into a file
    # This command uses the provided credentials to contact the server
    # and get a ticket which is used for authenticating future commands
    # think "browser login cookies", it also returns what permissions the user has. 
    cmd = 'curl -k -d "username={}&password={}"  https://{}:8006/api2/json/access/ticket > ./Data'.format(username,password,server)
    os.system(cmd)
    if (logLevle=="DEBUG"): print("Credentials obtaind for user {}".format(username))
  
    # Read dump file containing the output of the ticket request
    File = open("./Data","r")
    Data = File.read()
    File.close()
    #os.remove("Data")
    

    # Get Ticket
    # As the command returns not just the authentication ticket but also a bunch of permissions information,
    # we need to filter it outt. The ticket starts "ticket":" with and ends with " (inliding the " )
    Start = '"ticket":"'
    End = '"'
    Ticket = (Data.split(Start))[1].split(End)[0]
    if (logLevle=="DEBUG"): print("Ticket \"{}\"".format(Ticket))

    # Get Token
    # For added security, proxmox makes use of CSRF tokens which ensure each authentication can only be
    # used once. This token must be included in any requests we send to the server so we extract
    # it in the same way as the authentication token
    Start = '"CSRFPreventionToken":"'
    End = '"'
    Token = (Data.split(Start))[1].split(End)[0]
    if (logLevle=="DEBUG"): print("CSRF Token \"{}\"".format(Token))
  
    # Get proxy DATA
    # To connect to each VM, we are using the SPICE protocol, a type of remote desktop application.
    # This command connects to the server using the credentials which we just retrieved and requests the
    # information witch is used to initiate a SPICE connexion with the requested VM id
    cmd = 'curl -f -X POST -s -S -k -b "PVEAuthCookie={}" -H "CSRFPreventionToken: {}" https://{}:8006/api2/json/nodes/{}/qemu/{}/spiceproxy'.format(Ticket,Token,server,node,vm)
    if (logLevle=="DEBUG"): print("Command \"{}\"".format(cmd))


    # As this command is a bit more finicky and takes longer to run, we will use the "subprocess.run"
    # routine rather than "os.system" as it has better error handling.
    #
    # Just like the previous command, this one returns its result in Json format
    # This time we need to take the information and build the ".vv" file which
    # is used by the spice client on our machine to connect to the vm
    try:
        # Run command and read in the data
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        response = json.loads(result.stdout.decode())
        data = response['data']
    
        # Create .vv file content and add the data sources
        vv_content = f"""[virt-viewer]
type=spice
password={data['password']}
title=The lab
proxy={server}:3128
host={data['host']}
tls-port={data['tls-port']}
host-subject={data['host-subject']}
ca={data['ca']}
fullscreen=1
        """
        # Save to spiceproxy.vv
        with open("spiceproxy.vv", "w") as vv_file:
            vv_file.write(vv_content)
        print("spiceproxy.vv file generated successfully.")

    except subprocess.CalledProcessError as e:
        print("Error during API call:", e.stderr.decode())
    except json.JSONDecodeError:
        print("Invalid response from API.")

    

    # Connect
    # Launch the spice client, passing in the config that was just ceated
    cmd = r'"C:\Program Files (x86)\VirtViewer v11.0-256\bin\remote-viewer.exe" -f ./spiceproxy.vv'

    try:
        result = subprocess.run(cmd, shell=True, check=True)
        print("SPICE viewer launched successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error launching SPICE viewer: {e}")



getAUTH(username,password,server)

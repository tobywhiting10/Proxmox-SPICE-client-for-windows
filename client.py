##########################################
######        Vertion 2.0.0         ######
##########################################

##########################################
######        Vertion 2.0.0         ######
##########################################

import os
import subprocess
import json

server = "" # The address of the server to connect to
node = "" # the nodename of the server
vm = "" # the vm id to initiate a connexion with

username = "root" # username and password to authenticate to the server must have console permission 
relm = "pam"
password = ""
APIkey = "null" # not used yet

#path to folder contaning remote-viewer.exe
remoteViewerPath=r"C:\Program Files (x86)\VirtViewer v11.0-256\bin"
# Log Levle: NONE, ERROR, INFO, DEBUG
logLevle = "INFO"
SetionTitle="Proxmox SPICE client for windows"

def writeToLog(message,levle="INFO"):
    if (logLevle=="DEBUG"):
        print(message)
    elif (logLevle=="INFO" and (levle=="INFO" or levle=="ERROR")):
        print(message)
    elif (logLevle=="ERROR" and (levle=="ERROR")):
        print(message)
    else:
        if ((logLevle=="INFO" or logLevle=="DEBUG") and not (levle=="NONE" or levle=="ERROR" or levle=="INFO" or levle=="DEBUG")):
            print(message)

def getAUTH(username,password,relm,server):
    # Get Data from Proxmox Auth API and dump into a file
    # This command uses the provided credentials to contact the server
    # and get a ticket which is used for authenticating future commands
    # think "browser login cookies", it also returns what permissions the user has. 
    cmd = 'curl -k -d "username={}@{}&password={}"  https://{}:8006/api2/json/access/ticket > ./Data'.format(username,relm,password,server)
    os.system(cmd)
    writeToLog("Credentials obtaind for user {}".format(username),"INFO")
  
    # Read dump file containing the output of the ticket request
    File = open("./Data","r")
    Data = File.read()
    File.close()
    os.remove("Data")
    

    # Get Ticket
    # As the command returns not just the authentication ticket but also a bunch of permissions information,
    # we need to filter it outt. The ticket starts "ticket":" with and ends with " (inliding the " )
    Start = '"ticket":"'
    End = '"'
    Ticket = (Data.split(Start))[1].split(End)[0]
    writeToLog("Ticket \"{}\"".format(Ticket),"DEBUG")

    # Get Token
    # For added security, proxmox makes use of CSRF tokens which ensure each authentication can only be
    # used once. This token must be included in any requests we send to the server so we extract
    # it in the same way as the authentication token
    Start = '"CSRFPreventionToken":"'
    End = '"'
    Token = (Data.split(Start))[1].split(End)[0]
    writeToLog("CSRF Token \"{}\"".format(Token),"DEBUG")

    return [Ticket,Token]

def ConnectToSPICE(auth,server,node,VMid):
    # Get proxy DATA
    writeToLog("Atmpting to connect","INFO")
    # To connect to each VM, we are using the SPICE protocol, a type of remote desktop application.
    # This command connects to the server using the authorization ticket and requests the
    # information witch is used to initiate a SPICE connexion with the requested VM id
    cmd = 'curl -f -X POST -s -S -k -b "PVEAuthCookie={}" -H "CSRFPreventionToken: {}" https://{}:8006/api2/json/nodes/{}/qemu/{}/spiceproxy'.format(auth[0],auth[1],server,node,VMid)
    writeToLog("Command \"{}\"".format(cmd),"DEBUG")


    # As this command is a bit more finicky and takes longer to run, we will use the "subprocess.run"
    # routine rather than "os.system" as it has better error handling.
    #
    # Just like the previous command, this one returns its result in Json format
    # This time we need to take the information and build the ".vv" file which
    # is used by the spice client on our machine to connect to the vm
    try:
        # Run command and read in the data
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        response = json.loads(result.stdout.decode()) # read json
        data = response['data']

        # Create .vv file and add the reqierd content by
        # selectively picking information from the Json 
        vv_content = f"""[virt-viewer]
    type=spice
    password={data['password']}
    title={SetionTitle}
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
        writeToLog("spiceproxy.vv file generated successfully.", "INFO")

    except subprocess.CalledProcessError as e:
        writeToLog("Error during API call, do you have the right VM ID?: "+ e.stderr.decode(), "ERROR")
    except json.JSONDecodeError:
        writeToLog("Invalid response from API.", "ERROR")

    # Connect
    # Launch the spice client, passing in the config that was just ceated
    cmd = r'"{}\remote-viewer.exe" -f ./spiceproxy.vv'.format(remoteViewerPath)

    try:
        result = subprocess.run(cmd, shell=True, check=True)
        writeToLog("SPICE viewer launched successfully.", "INFO")
    except subprocess.CalledProcessError as e:
        writeToLog(f"Error launching SPICE viewer: {e}", "ERROR")



AuthenticationTiket = getAUTH(username,password,relm,server)
ConnectToSPICE(AuthenticationTiket,server,node,vm)
from pysnmp.entity import engine, config
from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.hlapi.asyncio import getCmd, setCmd, ObjectType, ObjectIdentity, CommunityData, UdpTransportTarget, SnmpEngine, ContextData
from pysnmp.entity.rfc3413 import ntfrcv
from threading import Thread
import asyncio
import logging


CLIENT_ADDRESS = '192.168.245.154'
CLIENT_PORT = 161
SERVER_ADDRESS = '192.168.245.154'
SERVER_PORT = 162


# Trap Receiver Handler
def handle_received_trap(snmpEngine, stateReference, contextEngineId, contextName, varBinds, cbCtx):
   
    logging.info("Received new Trap message")
    for name, val in varBinds:
        logging.info('%s = %s' % (name.prettyPrint(), val.prettyPrint()))
        
    logging.info("==== End of Incoming Trap ====")


# Function to start the SNMP trap listener on a separate thread
def trap_receiver():
    # SNMP Engine Initialization
    snmpEngine = engine.SnmpEngine()
    logging.basicConfig(
        filename='received_traps.log',
        filemode='w',
        format='%(asctime)s - %(message)s',
        level=logging.INFO
    )

    # Print server information
    logging.info(f"Server is listening SNMP Trap on {SERVER_ADDRESS}, Port: {SERVER_PORT}")
    logging.info('--------------------------------------------------------------------------')
    print(f"Server is listening SNMP Trap on {SERVER_ADDRESS}, Port: {SERVER_PORT}")

    # Configure transport for receiving traps
    config.addTransport(
        snmpEngine,
        udp.domainName + (1,),
        udp.UdpTransport().openServerMode((SERVER_ADDRESS, SERVER_PORT))
    )

    # Configure SNMPv1 community
    config.addV1System(snmpEngine, 'my-area', 'public')

    # Register trap handler
    ntfrcv.NotificationReceiver(snmpEngine, handle_received_trap)

    def run():
        try:
            snmpEngine.transportDispatcher.jobStarted(1)
            snmpEngine.transportDispatcher.runDispatcher()
        except Exception as e:
            snmpEngine.transportDispatcher.closeDispatcher()
            logging.error(f"Trap Listener Error: {e}")
            raise
    
    Thread(target=run, daemon=True).start()
    logging.info("Trap Listener thread started.")

def parse_oid(oid_str):
    if "::" in oid_str:
        parts = oid_str.split("::")
        mib, rest = parts[0], parts[1]
        identifiers = rest.split(".")
        return ObjectIdentity(mib, *identifiers)
    else:
        # Assume raw OID
        return ObjectIdentity(oid_str)

# Function to handle SNMP GET operation
async def snmp_get(target, oid_str):
    oid = parse_oid(oid_str)
    iterator = getCmd(
        SnmpEngine(),
        CommunityData('public', mpModel=0),  # SNMPv1 Community
        UdpTransportTarget((target, CLIENT_PORT)),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )
    errorIndication, errorStatus, errorIndex, varBinds = await iterator
    if errorIndication:
        print(f"Error: {errorIndication}")
    elif errorStatus:
        print(f"Error Status: {errorStatus.prettyPrint()}")
    else:
        for varBind in varBinds:
            print(f"GET Response: {varBind}")

# Function to handle SNMP SET operation
async def snmp_set(target, oid_str, value):
    oid = parse_oid(oid_str)
    iterator = setCmd(
        SnmpEngine(),
        CommunityData('public', mpModel=0),  # SNMPv1 Community
        UdpTransportTarget((target, CLIENT_PORT)),
        ContextData(),
        ObjectType(ObjectIdentity(oid), value)
    )
    errorIndication, errorStatus, errorIndex, varBinds = await iterator
    if errorIndication:
        print(f"Error: {errorIndication}")
    elif errorStatus:
        print(f"Error Status: {errorStatus.prettyPrint()}")
    else:
        for varBind in varBinds:
            print(f"SET Response: {varBind}")

# Function to parse user commands
def snmp_requester():
    print("Enter commands (e.g., 'get SNMPv2-MIB::sysDescr.0', or 'set SNMPv2-MIB::sysName.0 NewName'). Type 'exit' to quit.")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        command = input("> ").strip()
        if command.lower() == "exit":
            print("Exiting SNMP Server...")
            break
        parts = command.split()
        
        if len(parts) == 0:
            continue

        if len(parts) < 2:
            print("Invalid command. Use 'get <OID>' or 'set <OID> <value>'.")
            continue

        cmd, oid, *rest = parts
        target = CLIENT_ADDRESS  
        if cmd.lower() == "get":
            loop.run_until_complete(snmp_get(target, oid))
        elif cmd.lower() == "set":
            if not rest:
                print("SET command requires a value.")
                continue
            value = rest[0]
            loop.run_until_complete(snmp_set(target, oid, value))
        else:
            print("Unknown command. Use 'get' or 'set'.")

if __name__ == "__main__":

    # Start trap listener in a separate thread
    trap_receiver()
    
    # Run SNMP GET/SET requester 
    snmp_requester()

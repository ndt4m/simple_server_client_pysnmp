from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import cmdrsp, context
from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.hlapi.asyncio import sendNotification, NotificationType, CommunityData, UdpTransportTarget, ContextData, ObjectIdentity, OctetString
import threading
import asyncio
import time

CLIENT_ADDRESS = '192.168.245.154'
CLIENT_PORT = 161
SERVER_ADDRESS = '192.168.245.154'
SERVER_PORT = 162

def snmp_responder():
    """Sets up the SNMP responder for GET and SET requests."""

    # SNMP engine and context initialization
    snmpEngine = engine.SnmpEngine()

    # Transport setup
    config.addSocketTransport(
        snmpEngine,
        udp.domainName,
        udp.UdpTransport().openServerMode((CLIENT_ADDRESS, CLIENT_PORT))
    )

    # SecurityName <-> CommunityName mapping
    config.addV1System(snmpEngine, 'my-area', 'public')

    # Default context
    config.addContext(snmpEngine, '')

    # Allow full MIB access for the community
    config.addVacmUser(snmpEngine, 1, 'my-area', 'noAuthNoPriv', (1, 3, 6), (1, 3, 6))

    snmpContext = context.SnmpContext(snmpEngine)

    # Register SNMP Applications at the SNMP engine
    cmdrsp.GetCommandResponder(snmpEngine, snmpContext)
    cmdrsp.SetCommandResponder(snmpEngine, snmpContext)

    print("Starting agent...")
    snmpEngine.transportDispatcher.jobStarted(1)
    try:
        snmpEngine.transportDispatcher.runDispatcher()
    except:
        snmpEngine.transportDispatcher.closeDispatcher()
        raise


def trap_sender():
    """Sends an SNMP trap."""
    async def run():
        trapEngine = engine.SnmpEngine()
        errorIndication, errorStatus, errorIndex, varBinds = await sendNotification(
            trapEngine,
            CommunityData("public", mpModel=0),
            UdpTransportTarget((SERVER_ADDRESS, SERVER_PORT)),
            ContextData(),
            "trap",
            # Trap OID (SNMPv2-MIB::coldStart)
            NotificationType(ObjectIdentity("1.3.6.1.6.3.1.1.5.1")).addVarBinds(
                ("1.3.6.1.2.1.1.1", OctetString('Example Notificator')),
                ("1.3.6.1.2.1.1.5", OctetString("Notificator Example"))
            )
        )
        if errorIndication:
            print(f"Error sending trap: {errorIndication}")
        trapEngine.closeDispatcher()
    
    while True:
        time.sleep(10)
        asyncio.run(run())


if __name__ == '__main__':

    # Start the trap sender in a separate thread
    threading.Thread(target=trap_sender, daemon=True).start()

    # Run the SNMP responder
    try:
        snmp_responder()
    except KeyboardInterrupt:
        print("Shutting down...")

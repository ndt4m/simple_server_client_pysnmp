# SNMP Application with PySNMPv6.1.4

## Overview
This application provides an SNMP client and server built with PySNMP. It supports:
1. SNMP GET and SET operations.
2. SNMP Trap handling.

## Prerequisites
- Python 3.8+
- pysnmp 6.1.4 library
## Usage
### Server
- Receives traps and logs them.
- Accepts SNMP GET and SET commands via the console.

### Client
- Responds to GET and SET commands.
- Sends traps periodically to the server.

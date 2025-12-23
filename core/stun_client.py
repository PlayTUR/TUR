"""
STUN Client for TUR Multiplayer
<<<<<<< HEAD
Discovers external IP, port, and NAT type via STUN protocol.
=======
Discovers external IP and port via STUN protocol (RFC 5389).
Uses free Google STUN servers.
>>>>>>> 0dc16cc (use code wyind in the fortnite item shop)
"""

import socket
import struct
<<<<<<< HEAD
import os

STUN_BINDING_REQUEST = 0x0001
STUN_BINDING_RESPONSE = 0x0101
ATTR_XOR_MAPPED_ADDRESS = 0x0020
ATTR_MAPPED_ADDRESS = 0x0001
MAGIC_COOKIE = 0x2112A442

# NAT Types
NAT_OPEN = "OPEN"           # No NAT / Direct connection
NAT_FULL_CONE = "FULL_CONE" # Best for P2P
NAT_RESTRICTED = "RESTRICTED"  # Works with hole punching
NAT_SYMMETRIC = "SYMMETRIC"    # Problematic - different port per destination


def get_external_address(stun_host="stun.l.google.com", stun_port=19302, timeout=3.0, sock=None):
    """Query STUN server to discover external IP and port."""
    try:
        owned_sock = sock is None
        if owned_sock:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            sock.bind(('0.0.0.0', 0))
        
        # Create binding request
        transaction_id = os.urandom(12)
        request = struct.pack('>HHI', STUN_BINDING_REQUEST, 0, MAGIC_COOKIE) + transaction_id
        
        stun_addr = socket.gethostbyname(stun_host)
        sock.sendto(request, (stun_addr, stun_port))
        
        data, _ = sock.recvfrom(1024)
        
        # Parse response
        if len(data) < 20:
            return None, None, sock if not owned_sock else None
        
        msg_type = struct.unpack('>H', data[:2])[0]
        if msg_type != STUN_BINDING_RESPONSE:
            return None, None, sock if not owned_sock else None
        
        # Parse attributes
        pos = 20
        while pos < len(data):
            if pos + 4 > len(data):
                break
            attr_type, attr_len = struct.unpack('>HH', data[pos:pos+4])
            pos += 4
            if pos + attr_len > len(data):
                break
            
            if attr_type == ATTR_XOR_MAPPED_ADDRESS:
                xor_port = struct.unpack('>H', data[pos+2:pos+4])[0]
                port = xor_port ^ (MAGIC_COOKIE >> 16)
                xor_ip = struct.unpack('>I', data[pos+4:pos+8])[0]
                ip_int = xor_ip ^ MAGIC_COOKIE
                ip = socket.inet_ntoa(struct.pack('>I', ip_int))
                return ip, port, sock
            elif attr_type == ATTR_MAPPED_ADDRESS:
                port = struct.unpack('>H', data[pos+2:pos+4])[0]
                ip = socket.inet_ntoa(data[pos+4:pos+8])
                return ip, port, sock
            
            pos += attr_len + (4 - attr_len % 4) % 4
        
        return None, None, sock if not owned_sock else None
=======
import random
import os


# STUN Message Types
STUN_BINDING_REQUEST = 0x0001
STUN_BINDING_RESPONSE = 0x0101

# STUN Attributes
ATTR_MAPPED_ADDRESS = 0x0001
ATTR_XOR_MAPPED_ADDRESS = 0x0020

# Magic Cookie (RFC 5389)
MAGIC_COOKIE = 0x2112A442


def generate_transaction_id():
    """Generate random 12-byte transaction ID"""
    return os.urandom(12)


def create_binding_request():
    """Create a STUN Binding Request message"""
    msg_type = STUN_BINDING_REQUEST
    msg_length = 0  # No attributes in request
    transaction_id = generate_transaction_id()
    
    header = struct.pack('>HHI', msg_type, msg_length, MAGIC_COOKIE)
    return header + transaction_id, transaction_id


def parse_binding_response(data, transaction_id):
    """Parse STUN Binding Response and extract mapped address"""
    if len(data) < 20:
        return None
    
    # Parse header
    msg_type, msg_length, cookie = struct.unpack('>HHI', data[:8])
    resp_tid = data[8:20]
    
    # Verify response
    if msg_type != STUN_BINDING_RESPONSE:
        return None
    if resp_tid != transaction_id:
        return None
    
    # Parse attributes
    pos = 20
    while pos < len(data):
        if pos + 4 > len(data):
            break
        
        attr_type, attr_length = struct.unpack('>HH', data[pos:pos+4])
        pos += 4
        
        if pos + attr_length > len(data):
            break
        
        attr_value = data[pos:pos+attr_length]
        
        if attr_type == ATTR_XOR_MAPPED_ADDRESS:
            # XOR-MAPPED-ADDRESS (preferred)
            family = attr_value[1]
            xor_port = struct.unpack('>H', attr_value[2:4])[0]
            port = xor_port ^ (MAGIC_COOKIE >> 16)
            
            if family == 0x01:  # IPv4
                xor_ip = struct.unpack('>I', attr_value[4:8])[0]
                ip_int = xor_ip ^ MAGIC_COOKIE
                ip = socket.inet_ntoa(struct.pack('>I', ip_int))
                return ip, port
        
        elif attr_type == ATTR_MAPPED_ADDRESS:
            # MAPPED-ADDRESS (fallback)
            family = attr_value[1]
            port = struct.unpack('>H', attr_value[2:4])[0]
            
            if family == 0x01:  # IPv4
                ip = socket.inet_ntoa(attr_value[4:8])
                return ip, port
        
        # Move to next attribute (4-byte aligned)
        pos += attr_length
        pos = (pos + 3) & ~3
    
    return None


def get_external_address(stun_host="stun.l.google.com", stun_port=19302, timeout=3.0):
    """
    Query STUN server to discover external IP and port.
    Returns (external_ip, external_port, local_socket) or (None, None, None) on failure.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.bind(('0.0.0.0', 0))  # Bind to any available port
        
        # Resolve STUN server
        stun_addr = socket.gethostbyname(stun_host)
        
        # Send binding request
        request, transaction_id = create_binding_request()
        sock.sendto(request, (stun_addr, stun_port))
        
        # Receive response
        data, addr = sock.recvfrom(1024)
        
        result = parse_binding_response(data, transaction_id)
        if result:
            return result[0], result[1], sock
        
        sock.close()
        return None, None, None
        
>>>>>>> 0dc16cc (use code wyind in the fortnite item shop)
    except Exception as e:
        print(f"STUN Error: {e}")
        return None, None, None

<<<<<<< HEAD
=======

>>>>>>> 0dc16cc (use code wyind in the fortnite item shop)
def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
<<<<<<< HEAD
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def discover_external_address():
    """Try STUN servers until one works"""
    servers = [("stun.l.google.com", 19302), ("stun1.l.google.com", 19302)]
    for host, port in servers:
        result = get_external_address(host, port)
        if result[0]:
=======
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"


# STUN servers list for fallback
STUN_SERVERS = [
    ("stun.l.google.com", 19302),
    ("stun1.l.google.com", 19302),
    ("stun2.l.google.com", 19302),
    ("stun.stunprotocol.org", 3478),
]


def discover_external_address():
    """Try multiple STUN servers until one works"""
    for host, port in STUN_SERVERS:
        result = get_external_address(host, port)
        if result[0]:
            print(f"STUN success via {host}: {result[0]}:{result[1]}")
>>>>>>> 0dc16cc (use code wyind in the fortnite item shop)
            return result
    return None, None, None


<<<<<<< HEAD
def detect_nat_type(timeout=2.0):
    """
    Detect NAT type by querying multiple STUN servers.
    
    Returns:
        (nat_type, message, is_good_for_p2p)
        - nat_type: One of NAT_OPEN, NAT_FULL_CONE, NAT_RESTRICTED, NAT_SYMMETRIC
        - message: Human-readable description
        - is_good_for_p2p: True if P2P should work well
    """
    local_ip = get_local_ip()
    
    # First query
    ip1, port1, sock1 = get_external_address("stun.l.google.com", 19302, timeout)
    
    if not ip1:
        return NAT_SYMMETRIC, "Could not determine NAT type", False
    
    # Check if we're directly connected (no NAT)
    if ip1 == local_ip:
        return NAT_OPEN, "Direct connection - No NAT detected!", True
    
    # Second query with SAME socket to DIFFERENT server
    ip2, port2, _ = get_external_address("stun1.l.google.com", 19302, timeout, sock1)
    
    if sock1:
        sock1.close()
    
    if not ip2:
        return NAT_RESTRICTED, "Limited connectivity", True
    
    # Compare results
    if ip1 == ip2 and port1 == port2:
        return NAT_FULL_CONE, "Excellent connectivity", True
    elif ip1 == ip2 and port1 != port2:
        return NAT_SYMMETRIC, "Poor connectivity", False
    else:
        return NAT_RESTRICTED, "Limited connectivity", True


def get_nat_status_display():
    """Get a formatted status string for display with icons"""
    nat_type, message, good = detect_nat_type()
    
    # Icons and display names
    icons = {
        NAT_OPEN: ("📶", "OPEN"),
        NAT_FULL_CONE: ("🌐", "GOOD"),
        NAT_RESTRICTED: ("⚡", "OK"),
        NAT_SYMMETRIC: ("⚠", "LIMITED"),
    }
    
    icon, label = icons.get(nat_type, ("?", "UNKNOWN"))
    
    if good:
        return f"{icon} {label}: {message}", (100, 255, 100)
    else:
        return f"{icon} {label}: {message}", (255, 180, 80)


=======
if __name__ == "__main__":
    print("Testing STUN client...")
    ip, port, sock = discover_external_address()
    if ip:
        print(f"External address: {ip}:{port}")
        if sock:
            sock.close()
    else:
        print("Failed to discover external address")
>>>>>>> 0dc16cc (use code wyind in the fortnite item shop)

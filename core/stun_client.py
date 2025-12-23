"""
STUN Client for TUR Multiplayer
Discovers external IP and port via STUN protocol (RFC 5389).
Uses free Google STUN servers.
"""

import socket
import struct
import os

STUN_BINDING_REQUEST = 0x0001
STUN_BINDING_RESPONSE = 0x0101
ATTR_XOR_MAPPED_ADDRESS = 0x0020
ATTR_MAPPED_ADDRESS = 0x0001
MAGIC_COOKIE = 0x2112A442

# NAT Types
NAT_OPEN = "OPEN"
NAT_FULL_CONE = "FULL_CONE"
NAT_RESTRICTED = "RESTRICTED"
NAT_SYMMETRIC = "SYMMETRIC"

# STUN servers list for fallback
STUN_SERVERS = [
    ("stun.l.google.com", 19302),
    ("stun1.l.google.com", 19302),
    ("stun2.l.google.com", 19302),
    ("stun.stunprotocol.org", 3478),
]


def generate_transaction_id():
    """Generate random 12-byte transaction ID"""
    return os.urandom(12)


def create_binding_request():
    """Create a STUN Binding Request message"""
    msg_type = STUN_BINDING_REQUEST
    msg_length = 0
    transaction_id = generate_transaction_id()
    header = struct.pack('>HHI', msg_type, msg_length, MAGIC_COOKIE)
    return header + transaction_id, transaction_id


def parse_binding_response(data, transaction_id):
    """Parse STUN Binding Response and extract mapped address"""
    if len(data) < 20:
        return None
    
    msg_type, msg_length, cookie = struct.unpack('>HHI', data[:8])
    resp_tid = data[8:20]
    
    if msg_type != STUN_BINDING_RESPONSE:
        return None
    if resp_tid != transaction_id:
        return None
    
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
            family = attr_value[1]
            xor_port = struct.unpack('>H', attr_value[2:4])[0]
            port = xor_port ^ (MAGIC_COOKIE >> 16)
            
            if family == 0x01:  # IPv4
                xor_ip = struct.unpack('>I', attr_value[4:8])[0]
                ip_int = xor_ip ^ MAGIC_COOKIE
                ip = socket.inet_ntoa(struct.pack('>I', ip_int))
                return ip, port
        
        elif attr_type == ATTR_MAPPED_ADDRESS:
            family = attr_value[1]
            port = struct.unpack('>H', attr_value[2:4])[0]
            
            if family == 0x01:  # IPv4
                ip = socket.inet_ntoa(attr_value[4:8])
                return ip, port
        
        pos += attr_length
        pos = (pos + 3) & ~3
    
    return None


def get_external_address(stun_host="stun.l.google.com", stun_port=19302, timeout=3.0, sock=None):
    """
    Query STUN server to discover external IP and port.
    Returns (external_ip, external_port, local_socket) or (None, None, None) on failure.
    """
    try:
        owned_sock = sock is None
        if owned_sock:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            sock.bind(('0.0.0.0', 0))
        
        stun_addr = socket.gethostbyname(stun_host)
        request, transaction_id = create_binding_request()
        sock.sendto(request, (stun_addr, stun_port))
        
        data, addr = sock.recvfrom(1024)
        
        result = parse_binding_response(data, transaction_id)
        if result:
            return result[0], result[1], sock
        
        if owned_sock:
            sock.close()
        return None, None, None
        
    except Exception as e:
        print(f"STUN Error: {e}")
        return None, None, None


def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"


def discover_external_address():
    """Try multiple STUN servers until one works"""
    for host, port in STUN_SERVERS:
        result = get_external_address(host, port)
        if result[0]:
            print(f"STUN success via {host}: {result[0]}:{result[1]}")
            return result
    return None, None, None


def detect_nat_type(timeout=2.0):
    """
    Detect NAT type by querying multiple STUN servers.
    
    Returns:
        (nat_type, message, is_good_for_p2p)
    """
    local_ip = get_local_ip()
    
    ip1, port1, sock1 = get_external_address("stun.l.google.com", 19302, timeout)
    
    if not ip1:
        return NAT_SYMMETRIC, "Could not determine NAT type", False
    
    if ip1 == local_ip:
        return NAT_OPEN, "Direct connection - No NAT detected!", True
    
    ip2, port2, _ = get_external_address("stun1.l.google.com", 19302, timeout, sock1)
    
    if sock1:
        sock1.close()
    
    if not ip2:
        return NAT_RESTRICTED, "Limited connectivity", True
    
    if ip1 == ip2 and port1 == port2:
        return NAT_FULL_CONE, "Excellent connectivity", True
    elif ip1 == ip2 and port1 != port2:
        return NAT_SYMMETRIC, "Poor connectivity", False
    else:
        return NAT_RESTRICTED, "Limited connectivity", True


def get_nat_status_display():
    """Get a formatted status string for display with icons"""
    nat_type, message, good = detect_nat_type()
    
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


if __name__ == "__main__":
    print("Testing STUN client...")
    ip, port, sock = discover_external_address()
    if ip:
        print(f"External address: {ip}:{port}")
        if sock:
            sock.close()
    else:
        print("Failed to discover external address")

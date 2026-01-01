import asyncio
import httpx
import logging
from typing import Set
import ipaddress

logger = logging.getLogger("tur.blacklist")

# Default Feeds
# FireHOL Level 1: Aggressive (Bogon, Spamhaus DROP, Dshield, etc.)
# Emerging Threats: Known compromised hosts
FEEDS = [
    "https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/firehol_level1.netset",
    "https://rules.emergingthreats.net/fwrules/emerging-Block-IPs.txt"
]

class BlocklistManager:
    def __init__(self):
        self.blocked_ips: Set[str] = set()
        self.blocked_networks: list[ipaddress.IPv4Network] = [] # For CIDR
        self.running = False
        self.last_update = 0

    async def start_updater(self, interval_hours: int = 12):
        """Background task to update blocklists periodically."""
        self.running = True
        logger.info("Blocklist updater started.")
        while self.running:
            try:
                await self.fetch_blocklists()
            except Exception as e:
                logger.error(f"Failed to update blocklists: {e}")
            
            # Sleep for interval
            await asyncio.sleep(interval_hours * 3600)

    async def fetch_blocklists(self):
        """Fetches and parses all configured feeds."""
        logger.info("Fetching blocklists...")
        new_ips = set()
        new_nets = []

        async with httpx.AsyncClient() as client:
            for url in FEEDS:
                try:
                    resp = await client.get(url, timeout=10.0)
                    if resp.status_code == 200:
                        count = self._parse_feed(resp.text, new_ips, new_nets)
                        logger.info(f"Loaded {count} entries from {url}")
                    else:
                        logger.warning(f"Failed to fetch {url}: {resp.status_code}")
                except Exception as e:
                    logger.warning(f"Error fetching {url}: {e}")

        # Update atomic reference
        self.blocked_ips = new_ips
        self.blocked_networks = new_nets
        logger.info(f"Blocklist updated. Total blocked IPs: {len(self.blocked_ips)}, Networks: {len(self.blocked_networks)}")

    def _parse_feed(self, content: str, ip_set: set, net_list: list) -> int:
        count = 0
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith(('#', ';')):
                continue
            
            # Remove comments inline logic if needed, but usually lines are clean
            if ' ' in line:
                line = line.split()[0] # Take first part
            
            try:
                if '/' in line:
                    # CIDR
                    net = ipaddress.IPv4Network(line, strict=False)
                    net_list.append(net)
                else:
                    # Single IP
                    ipaddress.IPv4Address(line) # Validate
                    ip_set.add(line)
                count += 1
            except ValueError:
                continue # Skip invalid
        return count

    def check_ip(self, ip: str) -> bool:
        """Returns True if IP is blacklisted."""
        # 1. Fast Set Lookup
        if ip in self.blocked_ips:
            return True
        
        # 2. Network Scan (slower, but necessary for CIDR)
        # Optimization: Most requests are legit, so we only check if meaningful.
        # But malicious IPs must be blocked.
        # Check networks
        try:
            addr = ipaddress.IPv4Address(ip)
            for net in self.blocked_networks:
                if addr in net:
                    return True
        except ValueError:
            return False # Invalid IP provided
            
        return False

# Global instance
blocklist = BlocklistManager()

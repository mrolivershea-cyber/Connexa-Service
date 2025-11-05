#!/usr/bin/env python3

import re
import ipaddress

def debug_block_splitting():
    """Debug the block splitting logic for Format 4"""
    
    # Exact user data from review request
    user_data = """StealUrVPN
@StealUrVPN_bot

Ip: 71.84.237.32	a_reg_107
Login: admin
Pass: admin
State: California
City: Pasadena
Zip: 91101

Ip: 144.229.29.35
Login: admin
Pass: admin
State: California
City: Los Angeles
Zip: 90035
---------------------
GVBot
@gv2you_bot

76.178.64.46  admin admin CA
96.234.52.227  admin admin NJ
---------------------
Worldwide VPN Hub
@pptpmaster_bot

68.227.241.4 - admin:admin - Arizona/Phoenix 85001 | 2025-09-03 16:05:25
96.42.187.97 - 1:1 - Michigan/Lapeer 48446 | 2025-09-03 09:50:22

---------------------

PPTP INFINITY
@pptpinfinity_bot
70.171.218.52:admin:admin:US:Arizona:85001

> PPTP_SVOIM_VPN:
🚨 PPTP Connection
IP: 24.227.222.13
Credentials: admin:admin
Location: Texas (Austin)
ZIP: 78701

> PPTP_SVOIM_VPN:
🚨 PPTP Connection
IP: 71.202.136.233
Credentials: admin:admin
Location: California (Fremont)
ZIP: 94536

> PPTP_SVOIM_VPN:
🚨 PPTP Connection
IP: 24.227.222.112
Credentials: admin:admin
Location: Texas (Austin)
ZIP: 78701"""

    # Simulate the clean_text_data function
    def clean_text_data(text: str) -> str:
        """Clean and normalize text data - remove headers, mentions, comments"""
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip comment lines (starting with # or //)
            if line.startswith('#') or line.startswith('//'):
                continue
            
            # Skip Telegram channel mentions (lines starting with @)
            if line.startswith('@'):
                continue
            
            # Skip channel/group names (short lines with only letters/spaces, no colons or IPs)
            # Examples: "StealUrVPN", "GVBot", "Worldwide VPN Hub", "PPTP INFINITY"
            if len(line) < 50 and ':' not in line and not any(char.isdigit() for char in line):
                # Check if it looks like a header (mostly uppercase or title case)
                if line.isupper() or line.istitle() or all(c.isalpha() or c.isspace() for c in line):
                    continue
            
            # Remove inline comments (text after # or // in single-line formats)
            if '  #' in line:
                line = line.split('  #')[0].strip()
            elif '  //' in line:
                line = line.split('  //')[0].strip()
            
            # Remove multiple spaces, tabs, and normalize
            cleaned_line = ' '.join(line.split())
            
            if cleaned_line:
                lines.append(cleaned_line)
        
        return '\n'.join(lines)

    def is_valid_ip(ip: str) -> bool:
        """Basic IP validation"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    # Clean the data
    cleaned_data = clean_text_data(user_data)
    print("🧹 CLEANED DATA:")
    print("=" * 50)
    print(cleaned_data)
    print("=" * 50)
    
    # Simulate block splitting logic
    blocks = []
    
    # First, split by explicit separator
    if '---------------------' in cleaned_data:
        pre_blocks = cleaned_data.split('---------------------')
    else:
        pre_blocks = [cleaned_data]
    
    print(f"\n📦 PRE-BLOCKS (split by '---------------------'): {len(pre_blocks)}")
    for i, pre_block in enumerate(pre_blocks):
        print(f"\nPre-block {i+1}:")
        print(f"'{pre_block.strip()}'")
    
    # Now process each pre_block for further splitting
    for block_idx, pre_block in enumerate(pre_blocks):
        pre_block = pre_block.strip()
        if not pre_block:
            continue
        
        print(f"\n🔍 PROCESSING PRE-BLOCK {block_idx + 1}:")
        print(f"Content: '{pre_block}'")
        
        # Check if this pre_block contains multiple Format 1 entries (multiple "Ip:")
        if pre_block.count('Ip:') > 1 or pre_block.count('IP:') > 1:
            print("   → Contains multiple Format 1 entries (Ip:)")
            # Split by "Ip:" or "IP:" to separate multiple configs
            entries = re.split(r'(?=\bIp:|\bIP:)', pre_block, flags=re.IGNORECASE)
            for entry in entries:
                entry = entry.strip()
                if entry and ('Ip:' in entry or 'IP:' in entry):
                    blocks.append(entry)
                    print(f"     Added Format 1 block: '{entry[:50]}...'")
        
        # Check if this pre_block contains multiple Format 6 entries (PPTP header)
        elif pre_block.count('> PPTP_SVOIM_VPN:') > 1 or pre_block.count('🚨 PPTP Connection') > 1:
            print("   → Contains multiple Format 6 entries (PPTP header)")
            # Split by PPTP marker
            entries = re.split(r'(?=> PPTP_SVOIM_VPN:)', pre_block)
            for entry in entries:
                entry = entry.strip()
                if entry:
                    blocks.append(entry)
                    print(f"     Added Format 6 block: '{entry[:50]}...'")
        
        # Check if this looks like single-line format entries (Format 2, 3, 4)
        elif '\n' in pre_block:
            print("   → Contains newlines, checking for single-line formats")
            lines = pre_block.split('\n')
            multi_line_block = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                print(f"     Checking line: '{line}'")
                
                # Check Format 4: Colon-separated (IP:Login:Pass:Country:State:Zip)
                if line.count(':') >= 5 and is_valid_ip(line.split(':')[0]):
                    print(f"       → FOUND Format 4: '{line}'")
                    # This is Format 4 - single-line colon-separated
                    if multi_line_block:
                        blocks.append('\n'.join(multi_line_block))
                        print(f"       → Added multi-line block before Format 4: '{multi_line_block}'")
                        multi_line_block = []
                    blocks.append(line)
                    print(f"       → Added Format 4 block: '{line}'")
                    continue
                
                # Check Format 3: Dash format (IP - login:pass - State/City)
                if ' - ' in line and is_valid_ip(line.split()[0] if line.split() else ''):
                    print(f"       → FOUND Format 3: '{line}'")
                    # This is Format 3
                    if multi_line_block:
                        blocks.append('\n'.join(multi_line_block))
                        print(f"       → Added multi-line block before Format 3: '{multi_line_block}'")
                        multi_line_block = []
                    blocks.append(line)
                    print(f"       → Added Format 3 block: '{line}'")
                    continue
                
                # Check Format 2: Space-separated (IP Login Password State)
                parts = line.split()
                if len(parts) >= 3 and is_valid_ip(parts[0]):
                    print(f"       → FOUND Format 2: '{line}'")
                    # This is a single-line entry (Format 2)
                    if multi_line_block:
                        blocks.append('\n'.join(multi_line_block))
                        print(f"       → Added multi-line block before Format 2: '{multi_line_block}'")
                        multi_line_block = []
                    blocks.append(line)
                    print(f"       → Added Format 2 block: '{line}'")
                    continue
                
                # Not a single-line format - might be part of multi-line format
                print(f"       → Adding to multi-line block: '{line}'")
                multi_line_block.append(line)
            
            # Add any remaining multi-line block
            if multi_line_block:
                blocks.append('\n'.join(multi_line_block))
                print(f"     → Added final multi-line block: '{multi_line_block}'")
        
        else:
            print("   → Single block, no further splitting needed")
            # Single block
            blocks.append(pre_block)
    
    print(f"\n📋 FINAL BLOCKS: {len(blocks)}")
    for i, block in enumerate(blocks):
        print(f"\nBlock {i+1}:")
        print(f"'{block}'")
        
        # Detect format for each block
        def detect_format(block: str) -> str:
            """Detect which format the block matches"""
            lines = block.split('\n')
            
            # Format 6: Multi-line with PPTP header (ignore first 2 lines) - Check first
            if len(lines) >= 6 and ('PPTP_SVOIM_VPN' in lines[0] or 'PPTP Connection' in lines[1]):
                return "format_6"
            
            # Format 5: Multi-line with IP:, Credentials:, Location:, ZIP: - Check before Format 1
            if len(lines) >= 4 and any('IP:' in line for line in lines) and any('Credentials:' in line for line in lines):
                return "format_5"
            
            # Format 1: Key-value with colons (Ip: xxx, Login: xxx, Pass: xxx) - More specific check
            if any(line.strip().startswith(('Ip:', 'Login:', 'Pass:')) for line in lines):
                return "format_1"
            
            # Single line formats
            single_line = block.strip()
            
            # Format 3: With - and | separators
            if ' - ' in single_line and (' | ' in single_line or re.search(r'\d{4}-\d{2}-\d{2}', single_line)):
                return "format_3"
            
            # Format 4: Colon separated (5+ colons)
            if single_line.count(':') >= 4:
                return "format_4"
            
            # Format 2: Single line with spaces (IP Login Password State)
            parts = single_line.split()
            if len(parts) >= 4 and is_valid_ip(parts[0]):
                return "format_2"
            
            return "unknown"
        
        format_type = detect_format(block)
        print(f"   Format detected: {format_type}")
        
        if format_type == "format_4":
            print(f"   🎯 CRITICAL: Format 4 block found!")

if __name__ == "__main__":
    debug_block_splitting()
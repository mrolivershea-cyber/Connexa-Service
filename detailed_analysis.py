#!/usr/bin/env python3
"""
Detailed analysis of Format 6 parsing duplication
"""
import re

def is_valid_ip(ip: str) -> bool:
    """Check if string is valid IP"""
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False

def analyze_format6_blocks(file_path):
    """Analyze Format 6 block splitting"""
    print(f"=== ANALYZING FORMAT 6 BLOCKS: {file_path} ===\n")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Count markers
    pptp_svoim_count = text.count('> PPTP_SVOIM_VPN:')
    pptp_connection_count = text.count('🚨 PPTP Connection')
    
    print(f"Marker counts:")
    print(f"  > PPTP_SVOIM_VPN: {pptp_svoim_count}")
    print(f"  🚨 PPTP Connection: {pptp_connection_count}\n")
    
    # Split by > PPTP_SVOIM_VPN: (like the current parser does)
    entries = re.split(r'(?=> PPTP_SVOIM_VPN:)', text)
    print(f"Split by '> PPTP_SVOIM_VPN:' produces {len(entries)} entries\n")
    
    # Analyze first 5 entries
    print("First 5 entries analysis:")
    for i, entry in enumerate(entries[:5]):
        entry_preview = entry[:200].replace('\n', ' ')
        has_pptp_svoim = '> PPTP_SVOIM_VPN:' in entry
        has_pptp_connection = '🚨 PPTP Connection' in entry
        
        # Count how many IPs in this entry
        ip_matches = re.findall(r'IP:\s*(\d+\.\d+\.\d+\.\d+)', entry)
        
        print(f"\n  Entry {i}:")
        print(f"    Length: {len(entry)} chars")
        print(f"    Has '> PPTP_SVOIM_VPN:': {has_pptp_svoim}")
        print(f"    Has '🚨 PPTP Connection': {has_pptp_connection}")
        print(f"    Number of IPs found: {len(ip_matches)}")
        if ip_matches:
            print(f"    IPs: {ip_matches[:3]}")  # Show first 3 IPs
        print(f"    Preview: {entry_preview}...")
    
    # Extract all IPs from all entries
    all_ips = []
    for entry in entries:
        ip_matches = re.findall(r'IP:\s*(\d+\.\d+\.\d+\.\d+)', entry)
        all_ips.extend(ip_matches)
    
    unique_ips = set(all_ips)
    
    print(f"\n=== RESULTS ===")
    print(f"Total entries after split: {len(entries)}")
    print(f"Total IPs found: {len(all_ips)}")
    print(f"Unique IPs: {len(unique_ips)}")
    print(f"Duplication factor: {len(all_ips) / len(unique_ips) if unique_ips else 0:.2f}x")
    
    # Check for duplicates
    if len(all_ips) != len(unique_ips):
        from collections import Counter
        ip_counts = Counter(all_ips)
        duplicates = {ip: count for ip, count in ip_counts.items() if count > 1}
        print(f"\nDuplicated IPs found: {len(duplicates)}")
        print(f"Sample duplicates:")
        for ip, count in list(duplicates.items())[:5]:
            print(f"  {ip}: appears {count} times")

if __name__ == "__main__":
    analyze_format6_blocks("PPTP.txt")

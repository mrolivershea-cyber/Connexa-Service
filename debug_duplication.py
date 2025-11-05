#!/usr/bin/env python3
"""
Debug script to trace where node duplication occurs during parsing
"""
import sys
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

def parse_trace(file_path):
    """Parse file with detailed tracing"""
    print(f"=== DEBUG TRACE: {file_path} ===\n")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"STEP 1: Original text length: {len(text)} characters, {text.count(chr(10))} lines\n")
    
    # Step 2: Clean text
    cleaned = clean_text_data(text)
    print(f"STEP 2: After clean_text_data: {len(cleaned)} characters, {cleaned.count(chr(10))} lines")
    print(f"Sample of cleaned text (first 500 chars):\n{cleaned[:500]}\n")
    
    # Step 3: Split by '---------------------'
    if '---------------------' in cleaned:
        pre_blocks = cleaned.split('---------------------')
        print(f"STEP 3: Split by '---------------------': {len(pre_blocks)} pre_blocks")
    else:
        pre_blocks = [cleaned]
        print(f"STEP 3: No '---------------------' found, treating as single pre_block")
    
    # Step 4: Process each pre_block
    all_blocks = []
    for pre_idx, pre_block in enumerate(pre_blocks):
        pre_block = pre_block.strip()
        if not pre_block:
            continue
        
        print(f"\n  PRE_BLOCK {pre_idx + 1}: {len(pre_block)} characters, {pre_block.count(chr(10))} lines")
        
        # SUB-PASS 1: Extract single-line formats
        lines = pre_block.split('\n')
        single_line_blocks = []
        remaining_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            is_single_line = False
            
            # Check Format 7: Simple IP:Login:Pass (exactly 2 colons)
            parts_colon = line.split(':')
            if len(parts_colon) == 3 and is_valid_ip(parts_colon[0].strip()):
                single_line_blocks.append(line)
                is_single_line = True
            
            # Check Format 4: Colon-separated (at least 5 colons, starts with IP)
            elif len(parts_colon) >= 6 and is_valid_ip(parts_colon[0].strip()):
                single_line_blocks.append(line)
                is_single_line = True
            
            # Check Format 3: Dash format (IP - login:pass - State/City)
            elif ' - ' in line:
                parts_space = line.split()
                if parts_space and is_valid_ip(parts_space[0]):
                    single_line_blocks.append(line)
                    is_single_line = True
            
            # Check Format 2: Space-separated (IP Login Password State)
            elif not is_single_line:
                parts_space = line.split()
                if len(parts_space) >= 3 and is_valid_ip(parts_space[0]):
                    # Make sure it's not a line like "IP: xxx" (Format 1/5/6)
                    if ':' not in line or line.count(':') < 2:
                        single_line_blocks.append(line)
                        is_single_line = True
            
            # If not a single-line format, add to remaining for multi-line processing
            if not is_single_line:
                remaining_lines.append(line)
        
        print(f"    SUB-PASS 1: Extracted {len(single_line_blocks)} single-line blocks")
        print(f"    SUB-PASS 1: Remaining {len(remaining_lines)} lines for multi-line processing")
        
        # Add single-line blocks
        all_blocks.extend(single_line_blocks)
        
        # SUB-PASS 2: Process remaining lines for multi-line formats
        if remaining_lines:
            remaining_text = '\n'.join(remaining_lines)
            print(f"    SUB-PASS 2: Remaining text: {len(remaining_text)} characters")
            
            # Check for Format 6
            if '> PPTP_SVOIM_VPN:' in remaining_text or '🚨 PPTP Connection' in remaining_text:
                print(f"    SUB-PASS 2: Detected Format 6")
                if remaining_text.count('> PPTP_SVOIM_VPN:') > 1:
                    entries = re.split(r'(?=> PPTP_SVOIM_VPN:)', remaining_text)
                    print(f"    SUB-PASS 2: Split by '> PPTP_SVOIM_VPN:' into {len(entries)} entries")
                    for entry in entries:
                        entry = entry.strip()
                        if entry:
                            all_blocks.append(entry)
                elif remaining_text.count('🚨 PPTP Connection') > 1:
                    entries = re.split(r'(?=🚨 PPTP Connection)', remaining_text)
                    print(f"    SUB-PASS 2: Split by '🚨 PPTP Connection' into {len(entries)} entries")
                    for entry in entries:
                        entry = entry.strip()
                        if entry:
                            all_blocks.append(entry)
                else:
                    print(f"    SUB-PASS 2: Single Format 6 block")
                    all_blocks.append(remaining_text.strip())
            
            # Check for Format 1/5 (lowercase Ip:)
            elif remaining_text.count('Ip:') > 1:
                print(f"    SUB-PASS 2: Detected Format 1 (Ip:)")
                entries = re.split(r'(?=\bIp:)', remaining_text)
                print(f"    SUB-PASS 2: Split by 'Ip:' into {len(entries)} entries")
                for entry in entries:
                    entry = entry.strip()
                    if entry and 'Ip:' in entry:
                        all_blocks.append(entry)
            
            # Check for Format 5 (uppercase IP:)
            elif remaining_text.count('IP:') > 1:
                if 'Credentials:' in remaining_text and '> PPTP_SVOIM_VPN:' not in remaining_text:
                    print(f"    SUB-PASS 2: Detected Format 5 (IP: + Credentials:)")
                    entries = re.split(r'(?=\bIP:)', remaining_text)
                    print(f"    SUB-PASS 2: Split by 'IP:' into {len(entries)} entries")
                    for entry in entries:
                        entry = entry.strip()
                        if entry and 'IP:' in entry:
                            all_blocks.append(entry)
                else:
                    print(f"    SUB-PASS 2: Multiple IP: but not Format 5, treating as single block")
                    all_blocks.append(remaining_text.strip())
            
            # Single multi-line block
            elif remaining_text.strip():
                print(f"    SUB-PASS 2: Single multi-line block")
                all_blocks.append(remaining_text.strip())
    
    print(f"\n=== FINAL RESULT ===")
    print(f"Total blocks extracted: {len(all_blocks)}")
    
    # Count unique IPs in blocks
    unique_ips = set()
    for block in all_blocks:
        # Try to extract IP from block
        lines = block.split('\n')
        for line in lines:
            # Look for IP pattern
            ip_match = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', line)
            if ip_match:
                ip = ip_match.group(0)
                if is_valid_ip(ip):
                    unique_ips.add(ip)
                    break
    
    print(f"Unique IPs found: {len(unique_ips)}")
    print(f"Duplication factor: {len(all_blocks) / len(unique_ips) if unique_ips else 0:.2f}x")
    
    return all_blocks, unique_ips

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_duplication.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    blocks, unique_ips = parse_trace(file_path)

#!/usr/bin/env python3
"""
Analyze which pre-blocks contribute to duplication
"""
import sys
sys.path.insert(0, '/app/backend')

from server import clean_text_data, detect_format, is_valid_ip
import re

def analyze_file_structure(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    text_clean = clean_text_data(text)
    
    # Split by separator
    if '---------------------' in text_clean:
        pre_blocks = text_clean.split('---------------------')
    else:
        pre_blocks = [text_clean]
    
    print(f"Total pre-blocks: {len(pre_blocks)}\n")
    
    all_blocks = []
    
    for pre_idx, pre_block in enumerate(pre_blocks):
        pre_block = pre_block.strip()
        if not pre_block:
            continue
        
        print(f"=== PRE-BLOCK {pre_idx + 1} ===")
        print(f"Length: {len(pre_block)} chars")
        
        # Process this pre_block with TWO-PASS algorithm
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
            
            # Check Format 3: Dash format
            elif ' - ' in line:
                parts_space = line.split()
                if parts_space and is_valid_ip(parts_space[0]):
                    single_line_blocks.append(line)
                    is_single_line = True
            
            # Check Format 2: Space-separated
            elif not is_single_line:
                parts_space = line.split()
                if len(parts_space) >= 3 and is_valid_ip(parts_space[0]):
                    if ':' not in line or line.count(':') < 2:
                        single_line_blocks.append(line)
                        is_single_line = True
            
            if not is_single_line:
                remaining_lines.append(line)
        
        print(f"Single-line blocks extracted: {len(single_line_blocks)}")
        all_blocks.extend(single_line_blocks)
        
        # Process remaining for multi-line formats
        if remaining_lines:
            remaining_text = '\n'.join(remaining_lines)
            
            # Check for Format 6
            if '> PPTP_SVOIM_VPN:' in remaining_text or '🚨 PPTP Connection' in remaining_text:
                if remaining_text.count('> PPTP_SVOIM_VPN:') > 1:
                    entries = re.split(r'(?=> PPTP_SVOIM_VPN:)', remaining_text)
                    print(f"Format 6 blocks (split by '> PPTP_SVOIM_VPN:'): {len(entries)}")
                    all_blocks.extend([e for e in entries if e.strip()])
                elif remaining_text.count('🚨 PPTP Connection') > 1:
                    entries = re.split(r'(?=🚨 PPTP Connection)', remaining_text)
                    print(f"Format 6 blocks (split by '🚨 PPTP Connection'): {len(entries)}")
                    all_blocks.extend([e for e in entries if e.strip()])
                else:
                    print(f"Format 6 blocks (single): 1")
                    all_blocks.append(remaining_text.strip())
            
            # Check for Format 1/5
            elif remaining_text.count('Ip:') > 1:
                entries = re.split(r'(?=\bIp:)', remaining_text)
                print(f"Format 1 blocks: {len([e for e in entries if e.strip() and 'Ip:' in e])}")
                all_blocks.extend([e for e in entries if e.strip() and 'Ip:' in e])
            
            elif remaining_text.count('IP:') > 1:
                if 'Credentials:' in remaining_text and '> PPTP_SVOIM_VPN:' not in remaining_text:
                    entries = re.split(r'(?=\bIP:)', remaining_text)
                    print(f"Format 5 blocks: {len([e for e in entries if e.strip() and 'IP:' in e])}")
                    all_blocks.extend([e for e in entries if e.strip() and 'IP:' in e])
                else:
                    print(f"Multi-line block (single): 1")
                    all_blocks.append(remaining_text.strip())
            
            elif remaining_text.strip():
                print(f"Multi-line block (single): 1")
                all_blocks.append(remaining_text.strip())
        
        print()
    
    print(f"=== TOTAL BLOCKS: {len(all_blocks)} ===")
    return all_blocks

if __name__ == "__main__":
    blocks = analyze_file_structure('/app/PPTP.txt')
    
    # Count IPs in blocks
    ips = []
    for block in blocks:
        ip_match = re.search(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', block)
        if ip_match:
            ips.append(ip_match.group(1))
    
    print(f"\nTotal IPs found in blocks: {len(ips)}")
    print(f"Unique IPs: {len(set(ips))}")

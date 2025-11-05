#!/usr/bin/env python3

def parse_format_5_debug(block: str, node_data: dict) -> dict:
    """Debug Format 5: Multi-line with IP:, Credentials:, Location:, ZIP:"""
    print(f"Parsing block: {repr(block)}")
    lines = block.split('\n')
    print(f"Lines: {lines}")
    
    for line in lines:
        line = line.strip()
        print(f"Processing line: {repr(line)}")
        
        if line.startswith("IP:"):
            ip_value = line.split(':', 1)[1].strip()
            node_data['ip'] = ip_value
            print(f"  Set IP: {ip_value}")
        elif line.startswith("Credentials:"):
            creds = line.split(':', 1)[1].strip()
            print(f"  Credentials string: {repr(creds)}")
            if ':' in creds:
                login, password = creds.split(':', 1)
                node_data['login'] = login.strip()
                node_data['password'] = password.strip()
                print(f"  Set login: {login.strip()}, password: {password.strip()}")
            else:
                print(f"  No colon found in credentials: {creds}")
        elif line.startswith("Location:"):
            location = line.split(':', 1)[1].strip()
            print(f"  Location string: {repr(location)}")
            # Parse "State (City)" format
            if '(' in location and ')' in location:
                state = location.split('(')[0].strip()
                city = location.split('(')[1].split(')')[0].strip()
                node_data['state'] = state
                node_data['city'] = city
                print(f"  Set state: {state}, city: {city}")
        elif line.startswith("ZIP:"):
            zip_value = line.split(':', 1)[1].strip()
            node_data['zipcode'] = zip_value
            print(f"  Set zipcode: {zip_value}")
    
    print(f"Final node_data: {node_data}")
    return node_data

# Test the exact data from the review request
test_data = "IP: 24.227.222.13\nCredentials: admin:admin\nLocation: Texas (Austin)\nZIP: 78701"
node_data = {"protocol": "pptp", "status": "offline"}

result = parse_format_5_debug(test_data, node_data)
print(f"\nResult: {result}")
print(f"Has login: {bool(result.get('login'))}")
print(f"Has password: {bool(result.get('password'))}")
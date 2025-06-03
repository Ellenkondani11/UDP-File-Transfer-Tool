import socket


RECEIVER_IP = '0.0.0.10'
RECEIVER_PORT = 12345
BUFFER_SIZE = 1024

def start_receiver():
    print(f"Starting UDP receiver on {RECEIVER_IP}:{RECEIVER_PORT}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:

        sock.bind((RECEIVER_IP, RECEIVER_PORT))
        print("Waiting to receive messages...")

        while True:

            data, address = sock.recvfrom(BUFFER_SIZE)
            print(f"Received message from {address}: {data.decode('utf-8')}")

    except socket.error as e:
        print(f"Socket error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("Closing socket.")
        sock.close()

if __name__ == "__main__":
    start_receiver()
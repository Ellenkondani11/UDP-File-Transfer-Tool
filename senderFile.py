import socket
import os
import time

SENDER_IP = '0.0.0.0'
SENDER_PORT = 12347
RECEIVER_IP = '127.0.0.1'
RECEIVER_PORT = 12346
BUFFER_SIZE = 1024
CHUNK_SIZE = BUFFER_SIZE - 20

TIMEOUT = 0.5
MAX_RETRIES = 5


def send_file(file_path):
    print(f"Attempting to send file: {file_path}")

    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)


    total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE

    print(f"File: '{file_name}', Size: {file_size} bytes, Chunks: {total_chunks}")

    eof_message = f"EOF|{file_name}|{file_size}|{total_chunks}|".encode('utf-8')
    retries = 0
    ack_received = False
    while not ack_received and retries < MAX_RETRIES:
        try:
            print(f"Sending EOF message ({retries + 1}/{MAX_RETRIES})")
            sock.sendto(eof_message, (RECEIVER_IP, RECEIVER_PORT))

            data, _ = sock.recvfrom(BUFFER_SIZE)
            if data.decode('utf-8') == "ACK_EOF":
                print("ACK_EOF received. Starting file data transfer.")
                ack_received = True
        except socket.timeout:
            print("EOF ACK timed out. Retrying...")
            retries += 1
        except Exception as e:
            print(f"Error sending EOF: {e}")
            break

    if not ack_received:
        print("Failed to get ACK for EOF. Aborting file transfer.")
        sock.close()
        return

    sent_chunks = {}
    acknowledged_chunks = [False] * total_chunks

    with open(file_path, 'rb') as f:
        for i in range(total_chunks):
            chunk_data = f.read(CHUNK_SIZE)

            packet_data = f"{i}|{chunk_data.decode('latin-1')}".encode('utf-8')
            sent_chunks[i] = (packet_data, 0)

    all_chunks_acked = False
    while not all_chunks_acked:

        for seq_num in range(total_chunks):
            if not acknowledged_chunks[seq_num]:
                if seq_num in sent_chunks:
                    packet_data, current_retries = sent_chunks[seq_num]

                    if current_retries >= MAX_RETRIES:
                        print(f"Chunk {seq_num} failed after {MAX_RETRIES} retries. Aborting.")
                        sock.close()
                        return

                    print(f"Sending chunk {seq_num} (Retry: {current_retries})")
                    sock.sendto(packet_data, (RECEIVER_IP, RECEIVER_PORT))
                    sent_chunks[seq_num] = (packet_data, current_retries + 1)

        try:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            ack_parts = data.decode('utf-8').split('|')
            if ack_parts[0] == "ACK":
                acked_seq_num = int(ack_parts[1])
                if 0 <= acked_seq_num < total_chunks:
                    if not acknowledged_chunks[acked_seq_num]:
                        acknowledged_chunks[acked_seq_num] = True

                        if acked_seq_num in sent_chunks:
                            del sent_chunks[acked_seq_num]
                else:
                    print(f"Received invalid ACK sequence number: {acked_seq_num}")

        except socket.timeout:

            pass
        except Exception as e:
            print(f"Error receiving ACK: {e}")
            break

        all_chunks_acked = all(acknowledged_chunks)
        if not all_chunks_acked:
            time.sleep(0.1)

    print(f"File '{file_name}' sent and all chunks acknowledged.")

    sock.close()
    print("Sender socket closed.")


if __name__ == "__main__":
    dummy_file_name = "test_file.txt"
    dummy_content = "This is a test file for UDP transfer.\n" * 500
    with open(dummy_file_name, 'w') as f: import socket
import os
import time

SENDER_IP = '0.0.0.0'
SENDER_PORT = 12347
RECEIVER_IP = '127.0.0.1'
RECEIVER_PORT = 12346
BUFFER_SIZE = 1024
CHUNK_SIZE = BUFFER_SIZE - 20

TIMEOUT = 0.5
MAX_RETRIES = 5


def send_file(file_path):
    print(f"Attempting to send file: {file_path}")

    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)  # Set a timeout for receiving ACKs

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    # Calculate total chunks needed
    # ceil(file_size / CHUNK_SIZE)
    total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE

    print(f"File: '{file_name}', Size: {file_size} bytes, Chunks: {total_chunks}")

    eof_message = f"EOF|{file_name}|{file_size}|{total_chunks}|".encode('utf-8')
    retries = 0
    ack_received = False
    while not ack_received and retries < MAX_RETRIES:
        try:
            print(f"Sending EOF message ({retries + 1}/{MAX_RETRIES})")
            sock.sendto(eof_message, (RECEIVER_IP, RECEIVER_PORT))

            data, _ = sock.recvfrom(BUFFER_SIZE)
            if data.decode('utf-8') == "ACK_EOF":
                print("ACK_EOF received. Starting file data transfer.")
                ack_received = True
        except socket.timeout:
            print("EOF ACK timed out. Retrying...")
            retries += 1
        except Exception as e:
            print(f"Error sending EOF: {e}")
            break

    if not ack_received:
        print("Failed to get ACK for EOF. Aborting file transfer.")
        sock.close()
        return

    sent_chunks = {}
    acknowledged_chunks = [False] * total_chunks

    with open(file_path, 'rb') as f:
        for i in range(total_chunks):
            chunk_data = f.read(CHUNK_SIZE)

            packet_data = f"{i}|{chunk_data.decode('latin-1')}".encode('utf-8')
            sent_chunks[i] = (packet_data, 0)

    all_chunks_acked = False
    while not all_chunks_acked:

        for seq_num in range(total_chunks):
            if not acknowledged_chunks[seq_num]:
                if seq_num in sent_chunks:
                    packet_data, current_retries = sent_chunks[seq_num]

                    if current_retries >= MAX_RETRIES:
                        print(f"Chunk {seq_num} failed after {MAX_RETRIES} retries. Aborting.")
                        sock.close()
                        return

                    print(f"Sending chunk {seq_num} (Retry: {current_retries})")
                    sock.sendto(packet_data, (RECEIVER_IP, RECEIVER_PORT))
                    sent_chunks[seq_num] = (packet_data, current_retries + 1)

        try:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            ack_parts = data.decode('utf-8').split('|')
            if ack_parts[0] == "ACK":
                acked_seq_num = int(ack_parts[1])
                if 0 <= acked_seq_num < total_chunks:
                    if not acknowledged_chunks[acked_seq_num]:
                        acknowledged_chunks[acked_seq_num] = True

                        if acked_seq_num in sent_chunks:
                            del sent_chunks[acked_seq_num]
                else:
                    print(f"Received invalid ACK sequence number: {acked_seq_num}")

        except socket.timeout:

            pass
        except Exception as e:
            print(f"Error receiving ACK: {e}")
            break

        all_chunks_acked = all(acknowledged_chunks)
        if not all_chunks_acked:
            time.sleep(0.1)

    print(f"File '{file_name}' sent and all chunks acknowledged.")

    sock.close()
    print("Sender socket closed.")


if __name__ == "__main__":
    dummy_file_name = "test_file.txt"
    dummy_content = "This is a test file for UDP transfer.\n" * 500
    with open(dummy_file_name, 'w') as f:
        f.write(dummy_content)
    print(f"Created dummy file: {dummy_file_name}")

    send_file(dummy_file_name)

    f.write(dummy_content)
    print(f"Created dummy file: {dummy_file_name}")
    send_file(dummy_file_name)

import socket
import os

# Configuration
RECEIVER_IP = '0.0.0.0'
RECEIVER_PORT = 12346
BUFFER_SIZE = 1024
FILE_DIR = "received_files"


def start_file_receiver():
    print(f"Starting UDP File Receiver on {RECEIVER_IP}:{RECEIVER_PORT}")


    os.makedirs(FILE_DIR, exist_ok=True)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((RECEIVER_IP, RECEIVER_PORT))
    print("Waiting for file transfer...")

    received_data = {}
    expected_seq_num = 0
    file_name = None
    file_size = 0
    total_chunks = 0
    file_open = False
    output_file = None

    try:
        while True:
            try:

                data, sender_address = sock.recvfrom(BUFFER_SIZE)


                parts = data.decode('utf-8', errors='ignore').split('|', 1)


                if parts[0] == "EOF":
                    info_parts = parts[1].split('|')
                    file_name = info_parts[0]
                    file_size = int(info_parts[1])
                    total_chunks = int(info_parts[2])
                    print(f"Receiving file: '{file_name}' ({file_size} bytes, {total_chunks} chunks)")
                    print("Ready to receive data chunks...")


                    ack_message = f"ACK_EOF".encode('utf-8')
                    sock.sendto(ack_message, sender_address)
                    continue

                seq_num_str, chunk_data_str = parts
                seq_num = int(seq_num_str)


                received_data[seq_num] = chunk_data_str.encode(
                    'latin-1')

                # Send ACK back to sender
                ack_message = f"ACK|{seq_num}".encode('utf-8')
                sock.sendto(ack_message, sender_address)


                if seq_num == expected_seq_num:
                    if not file_open:

                        output_file_path = os.path.join(FILE_DIR, file_name)
                        output_file = open(output_file_path, 'wb')
                        file_open = True
                        print(f"Opened file for writing: {output_file_path}")

                    while expected_seq_num in received_data:
                        output_file.write(received_data[expected_seq_num])
                        del received_data[expected_seq_num]  # Remove written data
                        expected_seq_num += 1



                if file_name and expected_seq_num == total_chunks:
                    print(f"All {total_chunks} chunks received and written for '{file_name}'.")
                    if output_file:
                        output_file.close()
                        file_open = False
                    print(f"File '{file_name}' transfer complete. Saved to {os.path.join(FILE_DIR, file_name)}")


                    received_data = {}
                    expected_seq_num = 0
                    file_name = None
                    file_size = 0
                    total_chunks = 0
                    output_file = None
                    print("\nWaiting for new file transfer...")

            except socket.timeout:

                pass
            except Exception as e:
                print(f"Error processing packet: {e}")
                if file_open and output_file:
                    output_file.close()
                    file_open = False

    except KeyboardInterrupt:
        print("\nReceiver stopped by user.")
    except Exception as e:
        print(f"An unexpected error occurred in receiver: {e}")
    finally:
        if file_open and output_file:
            output_file.close()
            print("File closed due to receiver shutdown.")
        print("Closing socket.")
        sock.close()


if __name__ == "__main__":
    start_file_receiver()
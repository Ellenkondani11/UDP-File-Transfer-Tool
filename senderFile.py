import socket
import time


RECEIVER_IP = '127.0.0.1' #running the app on local IP
RECEIVER_PORT = 12345

def send_message(message):
    print(f"Sending message to {RECEIVER_IP}:{RECEIVER_PORT}")

    #created a socket that will not need to be bind to any IP and Port
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
       #encoding the message to be sent
        encoded_message = message.encode('utf-8')

       #sending the message to specified IP and Port as data
        sock.sendto(encoded_message, (RECEIVER_IP, RECEIVER_PORT))
        print("Message sent successfully.")

    except socket.error as e:
        print(f"Socket error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        #closing the socket after using it
        print("Closing socket.")
        sock.close()

if __name__ == "__main__":
    messages_to_send = [
        "Hello!",
        "This is a test message.",
        "Sending multiple packets.",
        "End of messages."
    ]

    for msg in messages_to_send:
        send_message(msg)
        time.sleep(1)
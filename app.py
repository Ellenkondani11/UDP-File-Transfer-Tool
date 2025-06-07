import wx
import socket
import os
import threading
import time

DEFAULT_RECEIVER_IP = '127.0.0.1'
DEFAULT_RECEIVER_PORT = 12346
DEFAULT_SENDER_PORT = 12347
BUFFER_SIZE = 1024
CHUNK_SIZE = BUFFER_SIZE - 20
TIMEOUT = 0.5
MAX_RETRIES = 5
RECEIVED_FILES_DIR = "received_files_gui"


os.makedirs(RECEIVED_FILES_DIR, exist_ok=True)


myEVT_UPDATE_STATUS_ID = wx.NewEventType()


class UpdateStatusEvent(wx.PyEvent):


    def __init__(self, data):
        wx.PyEvent.__init__(self, myEVT_UPDATE_STATUS_ID)
        self.data = data

#creating a class for our main frame of the app
class FileTransferFrame(wx.Frame):
    def __init__(self, parent, title):
        super(FileTransferFrame, self).__init__(parent, title=title, size=(800, 600))

        self.panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

#creating the sender section
        sender_static_box = wx.StaticBox(self.panel, label="Sender")
        sender_sizer = wx.StaticBoxSizer(sender_static_box, wx.VERTICAL)


        file_selection_sizer = wx.BoxSizer(wx.HORIZONTAL)
        file_selection_sizer.Add(wx.StaticText(self.panel, label="File Path:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                 5)
        self.file_path_text = wx.TextCtrl(self.panel, value="", size=(300, -1))
        file_selection_sizer.Add(self.file_path_text, 1, wx.EXPAND | wx.RIGHT, 5)
        browse_button = wx.Button(self.panel, label="Browse...")
        browse_button.Bind(wx.EVT_BUTTON, self.on_browse_file)
        file_selection_sizer.Add(browse_button, 0, wx.ALIGN_CENTER_VERTICAL)
        sender_sizer.Add(file_selection_sizer, 0, wx.EXPAND | wx.ALL, 5)


        receiver_info_sizer = wx.BoxSizer(wx.HORIZONTAL)
        receiver_info_sizer.Add(wx.StaticText(self.panel, label="Receiver IP:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
                                5)
        self.receiver_ip_text = wx.TextCtrl(self.panel, value=DEFAULT_RECEIVER_IP, size=(120, -1))
        receiver_info_sizer.Add(self.receiver_ip_text, 0, wx.RIGHT, 10)
        receiver_info_sizer.Add(wx.StaticText(self.panel, label="Port:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.receiver_port_text = wx.TextCtrl(self.panel, value=str(DEFAULT_RECEIVER_PORT), size=(80, -1))
        receiver_info_sizer.Add(self.receiver_port_text, 0)
        sender_sizer.Add(receiver_info_sizer, 0, wx.EXPAND | wx.ALL, 5)


        self.send_button = wx.Button(self.panel, label="Send File")
        self.send_button.Bind(wx.EVT_BUTTON, self.on_send_file)
        sender_sizer.Add(self.send_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        self.main_sizer.Add(sender_sizer, 0, wx.EXPAND | wx.ALL, 10)


        receiver_static_box = wx.StaticBox(self.panel, label="Receiver")
        receiver_sizer = wx.StaticBoxSizer(receiver_static_box, wx.VERTICAL)


        receiver_listen_port_sizer = wx.BoxSizer(wx.HORIZONTAL)
        receiver_listen_port_sizer.Add(wx.StaticText(self.panel, label="Listen Port:"), 0,
                                       wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.listen_port_text = wx.TextCtrl(self.panel, value=str(DEFAULT_RECEIVER_PORT), size=(80, -1))
        receiver_listen_port_sizer.Add(self.listen_port_text, 0)
        receiver_sizer.Add(receiver_listen_port_sizer, 0, wx.EXPAND | wx.ALL, 5)


        self.start_receiver_button = wx.Button(self.panel, label="Start Receiver")
        self.start_receiver_button.Bind(wx.EVT_BUTTON, self.on_start_receiver)
        receiver_sizer.Add(self.start_receiver_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        self.main_sizer.Add(receiver_sizer, 0, wx.EXPAND | wx.ALL, 10)


        status_static_box = wx.StaticBox(self.panel, label="Status Log")
        status_sizer = wx.StaticBoxSizer(status_static_box, wx.VERTICAL)
        self.status_log = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        status_sizer.Add(self.status_log, 1, wx.EXPAND | wx.ALL, 5)
        self.main_sizer.Add(status_sizer, 1, wx.EXPAND | wx.ALL, 10)

        self.panel.SetSizer(self.main_sizer)
        self.main_sizer.Layout()
        self.Centre()
        self.Show(True)


        self.Bind(wx.EVT_BUTTON, self.on_browse_file, browse_button)
        self.Bind(wx.EVT_BUTTON, self.on_send_file, self.send_button)
        self.Bind(wx.EVT_BUTTON, self.on_start_receiver, self.start_receiver_button)
        self.Bind(wx.PyEventBinder(myEVT_UPDATE_STATUS_ID, 1), self.on_update_status)

        self.receiver_thread = None
        self.sender_thread = None

    # this function will be triggered when the user clicks on Browse... button
    def on_browse_file(self, event):
        wildcard = "All files (*.*)|*.*"
        dialog = wx.FileDialog(self, "Choose a file", os.getcwd(), "", wildcard, wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            self.file_path_text.SetValue(dialog.GetPath())
        dialog.Destroy()

    # this function will be triggered when the user clicks on send file button
    def on_send_file(self, event):
        file_path = self.file_path_text.GetValue()
        receiver_ip = self.receiver_ip_text.GetValue()
        try:
            receiver_port = int(self.receiver_port_text.GetValue())
        except ValueError:
            self.update_status("Error: Invalid receiver port. Please enter a number.")
            return

        if not os.path.exists(file_path):
            self.update_status(f"Error: File not found at {file_path}")
            return

        self.send_button.Disable()
        self.update_status(f"Attempting to send '{os.path.basename(file_path)}' to {receiver_ip}:{receiver_port}...")


        self.sender_thread = threading.Thread(target=self._send_file_thread,
                                              args=(file_path, receiver_ip, receiver_port))
        self.sender_thread.daemon = True
        self.sender_thread.start()

    def on_start_receiver(self, event):
        try:
            listen_port = int(self.listen_port_text.GetValue())
        except ValueError:
            self.update_status("Error: Invalid listen port. Please enter a number.")
            return

        if self.receiver_thread and self.receiver_thread.is_alive():
            self.update_status("Receiver is already running.")
            return

        self.start_receiver_button.Disable()
        self.update_status(f"Starting receiver on port {listen_port}...")


        self.receiver_thread = threading.Thread(target=self._start_receiver_thread,
                                                args=(listen_port,))
        self.receiver_thread.daemon = True
        self.receiver_thread.start()

    def on_update_status(self, event):

        self.status_log.AppendText(event.data + "\n")

        self.status_log.ShowPosition(self.status_log.GetLastPosition())


    def update_status(self, message):

        evt = UpdateStatusEvent(message)
        wx.PostEvent(self, evt)


#this function will be used as the send file thread
    def _send_file_thread(self, file_path, receiver_ip, receiver_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(TIMEOUT)

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE

        self.update_status(f"Sender: File '{file_name}', Size: {file_size} bytes, Chunks: {total_chunks}")


        eof_message = f"EOF|{file_name}|{file_size}|{total_chunks}|".encode('utf-8')
        retries = 0
        ack_received = False
        while not ack_received and retries < MAX_RETRIES:
            try:
                self.update_status(f"Sender: Sending EOF message (Attempt {retries + 1}/{MAX_RETRIES})")
                sock.sendto(eof_message, (receiver_ip, receiver_port))

                data, _ = sock.recvfrom(BUFFER_SIZE)
                if data.decode('utf-8') == "ACK_EOF":
                    self.update_status("Sender: ACK_EOF received. Starting file data transfer.")
                    ack_received = True
            except socket.timeout:
                self.update_status("Sender: EOF ACK timed out. Retrying...")
                retries += 1
            except Exception as e:
                self.update_status(f"Sender: Error sending EOF: {e}")
                break

        if not ack_received:
            self.update_status("Sender: Failed to get ACK for EOF. Aborting file transfer.")
            sock.close()
            wx.CallAfter(self.send_button.Enable)
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
                            self.update_status(f"Sender: Chunk {seq_num} failed after {MAX_RETRIES} retries. Aborting.")
                            sock.close()
                            wx.CallAfter(self.send_button.Enable)
                            return

                        self.update_status(f"Sender: Sending chunk {seq_num} (Retry: {current_retries})")
                        sock.sendto(packet_data, (receiver_ip, receiver_port))
                        sent_chunks[seq_num] = (packet_data, current_retries + 1)

            try:
                data, _ = sock.recvfrom(BUFFER_SIZE)
                ack_parts = data.decode('utf-8').split('|')
                if ack_parts[0] == "ACK":
                    acked_seq_num = int(ack_parts[1])
                    if 0 <= acked_seq_num < total_chunks:
                        if not acknowledged_chunks[acked_seq_num]:
                            acknowledged_chunks[acked_seq_num] = True
                            self.update_status(f"Sender: ACK received for chunk {acked_seq_num}") # Too verbose
                            if acked_seq_num in sent_chunks:
                                del sent_chunks[acked_seq_num]
                    else:
                        self.update_status(f"Sender: Received invalid ACK sequence number: {acked_seq_num}") # Too verbose

            except socket.timeout:
                pass
            except Exception as e:
                self.update_status(f"Sender: Error receiving ACK: {e}")
                break

            all_chunks_acked = all(acknowledged_chunks)
            if not all_chunks_acked:
                time.sleep(0.01)

        self.update_status(f"Sender: File '{file_name}' sent and all chunks acknowledged.")
        sock.close()
        self.update_status("Sender: Socket closed.")
        wx.CallAfter(self.send_button.Enable)


#this function will be used as the start receiver thread
    def _start_receiver_thread(self, listen_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind(('0.0.0.0', listen_port))
            self.update_status(f"Receiver: Listening on port {listen_port}...")
        except socket.error as e:
            self.update_status(f"Receiver: Failed to bind to port {listen_port}: {e}")
            wx.CallAfter(self.start_receiver_button.Enable)
            return


        received_data = {}
        expected_seq_num = 0
        file_name = None
        file_size = 0
        total_chunks = 0
        output_file = None
        file_open_successful = False

        try:
            while True:
                data, sender_address = sock.recvfrom(BUFFER_SIZE)

                try:

                    parts = data.decode('utf-8', errors='ignore').split('|', 1)

                    if parts[0] == "EOF":
                        info_parts = parts[1].split('|')
                        file_name = info_parts[0]
                        file_size = int(info_parts[1])
                        total_chunks = int(info_parts[2])
                        self.update_status(
                            f"Receiver: Receiving file: '{file_name}' ({file_size} bytes, {total_chunks} chunks)")

                        ack_message = f"ACK_EOF".encode('utf-8')
                        sock.sendto(ack_message, sender_address)
                        self.update_status("Receiver: Sent ACK_EOF. Ready for data.")


                        output_file_path = os.path.join(RECEIVED_FILES_DIR, file_name)
                        try:
                            output_file = open(output_file_path, 'wb')
                            file_open_successful = True
                            self.update_status(f"Receiver: Opened file for writing: {output_file_path}")
                        except IOError as io_err:
                            self.update_status(f"Receiver: Error opening file '{output_file_path}': {io_err}")
                            file_open_successful = False
                        except Exception as e:
                            self.update_status(f"Receiver: Unexpected error opening file: {e}")
                            file_open_successful = False
                        continue


                    if not file_open_successful:
                        self.update_status("Receiver: File not opened successfully, discarding incoming data.")
                        continue

                    seq_num_str, chunk_data_str = parts
                    seq_num = int(seq_num_str)

                    received_data[seq_num] = chunk_data_str.encode('latin-1')

                    ack_message = f"ACK|{seq_num}".encode('utf-8')
                    sock.sendto(ack_message, sender_address)
                    self.update_status(f"Receiver: Received chunk {seq_num}. Sent ACK.")

                    if seq_num == expected_seq_num:
                        while expected_seq_num in received_data:
                            if output_file:
                                output_file.write(received_data[expected_seq_num])
                                del received_data[expected_seq_num]
                                expected_seq_num += 1
                                self.update_status(f"Receiver: Wrote chunk {expected_seq_num - 1}.")
                            else:
                                self.update_status("Receiver: Output file not open, cannot write chunk.")
                                break

                    if file_name and expected_seq_num == total_chunks:
                        self.update_status(
                            f"Receiver: All {total_chunks} chunks received and written for '{file_name}'.")
                        if output_file:
                            output_file.close()
                            output_file = None
                        self.update_status(
                            f"Receiver: File '{file_name}' transfer complete. Saved to {os.path.join(RECEIVED_FILES_DIR, file_name)}")


                        received_data = {}
                        expected_seq_num = 0
                        file_name = None
                        file_size = 0
                        total_chunks = 0
                        file_open_successful = False
                        self.update_status("\nReceiver: Waiting for new file transfer...")

                except Exception as e:
                    self.update_status(f"Receiver: Error processing packet: {e}")

                    if output_file:
                        output_file.close()
                        output_file = None
                    file_open_successful = False

        except KeyboardInterrupt:
            self.update_status("\nReceiver: Stopped by user.")
        except Exception as e:
            self.update_status(f"Receiver: An unexpected error occurred: {e}")
        finally:
            if output_file:
                output_file.close()
                self.update_status("Receiver: Output file closed due to receiver shutdown.")
            self.update_status("Receiver: Socket closed.")
            sock.close()
            wx.CallAfter(self.start_receiver_button.Enable)



class FileTransferApp(wx.App):
    def OnInit(self):
        self.frame = FileTransferFrame(None, "UDP File Transfer Tool")
        return True



if __name__ == '__main__':
    app = FileTransferApp()
    app.MainLoop()
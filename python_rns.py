# python3 -m venv ~/venv_can
# source ~/venv_can/bin/activate
# python -m pip install --upgrade pip
# python -m pip install python-can
# python -m pip install pyserial
# Candlelight firmware on Linux
#bus = can.interface.Bus(interface='socketcan', channel='can0', bitrate=500000)
import can
import serial
import logging
import time

# Cấu hình logging để debug
logging.basicConfig(level=logging.DEBUG)
can.util.set_logging_level('DEBUG')


# Cấu hình thiết bị
CHANNEL = '/dev/tty.usbmodem2054306053301'  # Thay đổi theo cổng của bạn
# can.exceptions.CanInitializationError: Invalid bitrate, choose one of 10000, 20000, 50000, 100000, 125000, 250000, 500000, 750000, 1000000, 83300.
BITRATE = 125000


# Danh sách các ID CAN đã biết để bỏ qua
ignore_ids = {
    0x99999,

    # 0x2F7, 0x355, 0x0F9, 0x003, 0x004, 0x388, 0x414, 0x045, 0x007, 0x382, 0x31F,
    # 0x205, 0x069, 0x105, 0x04B, 0x02F, 0x12D, 0x1C0, 0x006, 0x001, 0x0F8,
    # 0x0FE, 0x0FF, 0x0DE, 0x37D, 0x41E, 0x35C, 0x10E, 0x015, 0x18B, 0x3D1,
    # 0x3D3, 0x239, 0x321, 0x025, 0x175, 0x62F, 0x3FC, 0x141, 0x30E, 0x2E9, 0x231,
    # 0x200, 0x369, 0x420, 0x2FB, 0x30C, 0x421, 0x1C1, 0x26F, 0x10D,
    # 0x3F6, 0x245, 0x37B, 0x3BF, 0x3BB, 0x385, 0x339, 0x0BC, 0x423, 0x10C, 0x0BB,
    # # 0x20B, 0x002, 0x203,
    # 0x1E0, 0x206, 0x207, 0x208, 0x401, 0x402, 0x19F, 0x204, 0x325, 0x40A, 0x39F, 
    # 0x3B7, 0x3B8, 0x41F, 0x3E1, 0x3E2, 0x5D4, 0x5E0, 0x5E1, 0x5E2, 0x3FB, 0x5E3, 
    # 0x629, 0x422, 0x5DE,
}

# Khi bật chìa khóa
# ignore_ids.update({
#     0x371, 0x373, 0x2EE
# })

def init_slcan():
    """Khởi tạo SLCAN với retry"""
    max_retries = 3
    retry_delay = 1.0  # seconds
    
    for attempt in range(max_retries):
        try:
            # Đợi thiết bị sẵn sàng
            time.sleep(retry_delay)
            
            print(f"Opening serial port {CHANNEL} (attempt {attempt + 1}/{max_retries})...")
            ser = serial.Serial(CHANNEL, 115200, timeout=1)
            
            # Reset device
            ser.write(b'C\r')  # Close port if open
            time.sleep(0.1)
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            
            # Set bitrate và mở kênh
            print("Sending SLCAN commands...")
            ser.write(b'S9\r')  # 83.3kbps
            time.sleep(0.1)
            response = ser.readline().decode(errors='ignore').strip()
            if not response.startswith('\r'):
                print(f"Bitrate response: {response}")
            
            ser.write(b'O\r')   # Open channel
            time.sleep(0.1)
            response = ser.readline().decode(errors='ignore').strip()
            if not response.startswith('\r'):
                print(f"Open channel response: {response}")
            
            if 'ERR:' in response:
                raise Exception("Firmware reported error during initialization")
            
            # Đóng serial để python-can có thể sử dụng
            ser.close()
            time.sleep(0.5)  # Đợi lâu hơn trước khi mở lại
            return True
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                raise Exception("Failed to initialize SLCAN after multiple attempts")

# Hàm gửi tin nhắn tại đây!
def send_can_message(bus, arbitration_id, data, extended=False):
    """Gửi tin nhắn CAN"""
    try:
        msg = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=extended)
        bus.send(msg)
        print(f"Message sent on {bus.channel_info}: ID=0x{arbitration_id:03X}, Data={data}, Extended={extended}")
    except can.CanError as e:
        print(f"Failed to send message: {e}")
        logging.exception("Failed to send message")



##### BẮT ĐẦU ####################################

try:
    # Khởi tạo SLCAN
    if not init_slcan():
        raise Exception("Failed to initialize SLCAN")

    print(f"Initializing CAN bus on {CHANNEL} at {BITRATE} bps...")
    
    # Khởi tạo bus với slcan
    bus = can.interface.Bus(
        interface='slcan',
        channel=CHANNEL,
        bitrate=BITRATE,
        sleep_after_open=1.0  # Tăng thời gian đợi lên 1 giây
    )
    
    print("CAN bus initialized successfully")
    print("Listening for CAN messages...\n")



    # Đọc tin nhắn
    while True:
        try:
            msg = bus.recv(timeout=1.0)
            if msg:
             # Bỏ qua các ID đã biết
                if msg.arbitration_id in ignore_ids:
                    continue
                # In ra theo định dạng hex cho ID và data
                data_hex = ' '.join(f'{b:02X}' for b in msg.data)
                print(f"ID: 0x{msg.arbitration_id:03X} [{msg.dlc}] Data: {data_hex}")
            else:
                print(f"Waiting for messages...")

            time.sleep(0.5)
            
        except KeyboardInterrupt:
            print("\nStopping...")
            break
            
except Exception as e:
    print(f"Error: {e}")
    logging.exception("Error occurred")
    
finally:
    try:
        if 'bus' in locals():
            print("Shutting down CAN bus...")
            bus.shutdown()
    except Exception as e:
        print(f"Error during shutdown: {e}")
        logging.exception("Error during shutdown")
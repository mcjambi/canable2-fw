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




##### BẮT ĐẦU ####################################

# Thư viện các tin nhắn CAN đã biết
library = {
    "0x029_len:3_data:50 22 05": "Xi nhan",
    "0x1ED_len:8_data:20 21 13 18 47 14 82 FD": "Bấm mở trên chìa",
    "0x1ED_len:8_data:20 23 14 18 47 14 82 5F": "Bấm khóa trên chìa",
    "0x1ED_len:8_data:20 45 18 18 47 14 82 75": "Bấm mở cốp trên chìa",
    "0x141_len:8_data:00 B1 7C FF 00 00 FF 00": "Rút chìa khỏi ổ khóa",
    "0x402_len:8_data:FE 02 04 02 18 FF FF 06": "Cắm chìa vào ổ khóa",
}

def format_can_message(msg):
    """Định dạng tin nhắn CAN thành chuỗi để so sánh với thư viện"""
    data_hex = ' '.join(f'{b:02X}' for b in msg.data)
    return f"0x{msg.arbitration_id:03X}_len:{msg.dlc}_data:{data_hex}"

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
    print("Đang theo dõi các sự kiện:")
    for key, value in library.items():
        print(f"- {value}: {key}")
    print("\nBắt đầu nhận tin nhắn...")

    # Đọc tin nhắn
    while True:
        try:
            msg = bus.recv(timeout=0.1)
            if msg:
                # Định dạng tin nhắn
                msg_str = format_can_message(msg)
                
                # Chỉ hiển thị tin nhắn có trong thư viện
                if msg_str in library:
                    print(f"\n==> Phát hiện sự kiện: {library[msg_str]}")
                    print(f"    Chi tiết: {msg_str}")
            
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



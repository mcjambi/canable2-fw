import can
import time
import sys
import logging
from datetime import datetime

# Cấu hình thiết bị
CHANNEL = '/dev/tty.usbmodem2054306053301'  # Thay đổi theo cổng của bạn
BITRATE = 125000

# Danh sách các ID CAN cần theo dõi
MONITOR_IDS = {}

# Danh sách các ID CAN cần bỏ qua
IGNORE_IDS = {0x333333}

def init_can():
    """Khởi tạo kết nối CAN"""
    try:
        bus = can.interface.Bus(
            interface='slcan',
            channel=CHANNEL,
            bitrate=BITRATE
        )
        print("Đã kết nối CAN thành công")
        return bus
    except Exception as e:
        print(f"Lỗi kết nối CAN: {e}")
        return None

def setup_logging():
    """Thiết lập logging"""
    # Tạo tên file log với timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"canbus_{timestamp}.log"
    
    # Cấu hình logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),  # Ghi vào file
            logging.StreamHandler()  # Hiển thị trên console
        ]
    )
    
    print(f"Đang ghi log vào file: {log_filename}")
    return log_filename

def main():
    # Khởi tạo kết nối CAN
    bus = init_can()
    if not bus:
        return

    # Thiết lập logging
    log_file = setup_logging()
    
    print("Bắt đầu ghi log tin nhắn CAN...")
    print("Đang theo dõi các ID CAN:")
    for id in sorted(MONITOR_IDS):
        print(f"- 0x{id:03X}")
    print("\nBỏ qua các ID CAN:")
    for id in sorted(IGNORE_IDS):
        print(f"- 0x{id:03X}")
    print("\nNhấn Ctrl+C để dừng")
    
    try:
        while True:
            msg = bus.recv(timeout=1.0)
            if msg:
                # Bỏ qua các ID trong danh sách ignore
                if msg.arbitration_id in IGNORE_IDS:
                    continue
                    
                # Nếu có ID trong danh sách theo dõi thì chỉ log các ID đó
                # Nếu không có ID nào trong danh sách theo dõi thì log tất cả
                if not MONITOR_IDS or msg.arbitration_id in MONITOR_IDS:
                    # Chuyển data thành chuỗi hex
                    data_hex = ' '.join(f'{b:02X}' for b in msg.data)
                    
                    # Tạo chuỗi log theo định dạng giống python_replay.py
                    log_msg = f"ID: 0x{msg.arbitration_id:03X} [{msg.dlc}] Data: {data_hex}"
                    
                    # Ghi vào log
                    logging.info(log_msg)
                
    except KeyboardInterrupt:
        print("\nĐã dừng ghi log")
    finally:
        bus.shutdown()
        print(f"Log đã được lưu vào: {log_file}")

if __name__ == "__main__":
    main()

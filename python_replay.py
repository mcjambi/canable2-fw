import can
import time
import sys

# Danh sách các cụm tin nhắn, mỗi cụm là một chuỗi các tin nhắn
MESSAGE_GROUPS = [
    """ID: 0x400 [8] Data: FE 00 04 02 0B 00 00 06
ID: 0x201 [8] Data: FF FF FF FF FF 00 00 FF
ID: 0x375 [8] Data: 01 37 3F 00 00 07 02 00
ID: 0x41F [8] Data: FE 1F 04 02 00 00 00 06
ID: 0x203 [8] Data: FF FF FF FF FF FF FF FF
ID: 0x421 [8] Data: FE 21 04 02 00 00 00 06
ID: 0x420 [8] Data: FE 20 04 02 00 00 00 06
ID: 0x007 [8] Data: 50 05 38 00 3F FC FF 79
ID: 0x00F [1] Data: 01"""
]

# Cấu hình thiết bị
CHANNEL = '/dev/tty.usbmodem2054306053301'  # Thay đổi theo cổng của bạn
BITRATE = 125000

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

def parse_message(line):
    """Phân tích cú pháp một dòng tin nhắn"""
    try:
        # Format: ID: 0x029 [3] Data: 50 22 05
        parts = line.split()
        id_hex = int(parts[1], 16)  # Chuyển 0x029 thành số
        data_hex = ' '.join(parts[4:])  # Lấy phần data
        return id_hex, data_hex
    except Exception as e:
        print(f"Lỗi phân tích cú pháp: {e}")
        return None

def send_can_message(bus, id_hex, data_hex):
    """Gửi tin nhắn CAN với ID và data dạng hex"""
    try:
        # Chuyển đổi chuỗi hex thành bytes
        data = bytes.fromhex(data_hex.replace(" ", ""))
        
        # Tạo và gửi tin nhắn
        msg = can.Message(
            arbitration_id=id_hex,
            data=data,
            is_extended_id=False
        )
        bus.send(msg)
        print(f"ID: 0x{id_hex:03X} [{len(data)}] Data: {' '.join(f'{b:02X}' for b in data)}")
        
    except Exception as e:
        print(f"Lỗi gửi tin nhắn: {e}")

def send_message_group(bus, group):
    """Gửi một cụm tin nhắn liên tiếp"""
    # Tách các dòng tin nhắn trong cụm
    message_lines = [line.strip() for line in group.split('\n') if line.strip()]
    
    print(f"\nBắt đầu gửi cụm tin nhắn ({len(message_lines)} tin nhắn):")
    for line in message_lines:
        print(f"- {line}")
    
    # Gửi từng tin nhắn trong cụm
    for line in message_lines:
        message = parse_message(line)
        if message:
            id_hex, data_hex = message
            send_can_message(bus, id_hex, data_hex)
            time.sleep(1)  # Đợi 100ms giữa các tin nhắn

def main():
    # Khởi tạo kết nối CAN
    bus = init_can()
    if not bus:
        return

    print("Bắt đầu phát lại tin nhắn...")
    print("Nhấn Enter để gửi cụm tin nhắn tiếp theo, Ctrl+C để dừng")
    
    try:
        current_group = 0
        while True:
            # Lấy cụm tin nhắn tiếp theo
            group = MESSAGE_GROUPS[current_group]
            print(f"\nCụm tin nhắn tiếp theo ({current_group + 1}/{len(MESSAGE_GROUPS)}):")
            print(group)
            
            # Đợi người dùng nhấn Enter
            input("Nhấn Enter để gửi cụm tin nhắn...")
            
            # Gửi cụm tin nhắn
            send_message_group(bus, group)
            
            # Chuyển đến cụm tin nhắn tiếp theo
            current_group = (current_group + 1) % len(MESSAGE_GROUPS)
            
    except KeyboardInterrupt:
        print("\nĐã dừng phát lại")
    finally:
        bus.shutdown()

if __name__ == "__main__":
    main()

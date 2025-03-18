import can
import time
import sys

# Danh sách các cụm tin nhắn, mỗi cụm là một chuỗi các tin nhắn
MESSAGE_GROUPS = [
    """ID: 0x3D3 [4] Data: C9 00 00 00
ID: 0x41F [8] Data: FD 20 3F FF FF FF FF FF
ID: 0x02F [7] Data: 00 00 64 00 00 00 00
ID: 0x3B7 [8] Data: 3C 00 07 FF 00 03 FF FF
ID: 0x006 [5] Data: 00 3C 00 FF 02
ID: 0x007 [8] Data: 50 05 38 00 3F FC FF 79
ID: 0x30C [2] Data: 00 00
ID: 0x382 [3] Data: 00 00 00
ID: 0x3F6 [5] Data: 02 00 00 00 00
ID: 0x045 [8] Data: 00 FF 00 00 00 00 07 FF
ID: 0x208 [8] Data: 19 00 00 00 00 00 00 3C
ID: 0x3FC [2] Data: 3C 00
ID: 0x12D [8] Data: 00 90 50 55 18 47 14 82
ID: 0x3FB [2] Data: 15 50
ID: 0x04B [6] Data: 00 C1 CF 3E C1 00
ID: 0x205 [8] Data: 02 7B 08 0F 00 00 00 00
ID: 0x141 [8] Data: 00 A1 70 FF 00 00 FF 00
ID: 0x629 [8] Data: 33 00 00 00 00 00 00 00
ID: 0x00F [1] Data: 00"""
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
            time.sleep(0.02)  # Đợi 100ms giữa các tin nhắn

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

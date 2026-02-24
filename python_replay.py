import can
import time
import sys

# gõ source venv/bin/activate trước
# pip install pyserial
# pip install python-can
# python python_replay.py

# Danh sách tin nhắn (mỗi lần Enter sẽ gửi 1 tin nhắn)
MESSAGES = [
    """ID: 0x001 [8] Data: 00 C0 DF AC AA 07 22 02""", # On xe
    """ID: 0x001 [8] Data: 00 C0 DF 5C 55 07 22 02""", # Off xe
    """ID: 0x12D [8] Data: 02 60 00 00 00 00 00 00""", # Off xe bằng chìa
    """ID: 0x12D [8] Data: 02 60 00 00 00 00 00 00""", # Off xe bằng chìa
    """ID: 0x12D [8] Data: 02 90 00 00 00 00 00 00""", # Mở xe bằng chìa
    # """ID: 0x001 [8] Data: 00 C0 DF AC AA 07 22 02""", # On xe
    # """ID: 0x388 [8] Data: 07 FF 07 00 00 1F FF 3F""", # số lùi
    # """ID: 0x388 [8] Data: 05 FF 07 00 00 1F FF 3F""", # số D
    # """ID: 0x388 [8] Data: 08 FF 07 00 00 1F FF 3F""", # số P
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

def send_message_line(bus, line):
    """Gửi một tin nhắn"""
    message = parse_message(line)
    if message:
        id_hex, data_hex = message
        send_can_message(bus, id_hex, data_hex)

def main():
    # Khởi tạo kết nối CAN
    bus = init_can()
    if not bus:
        return

    print("Bắt đầu phát lại tin nhắn...")
    print("Nhấn Enter để gửi tin nhắn tiếp theo, gõ q để dừng")
    
    try:
        current_index = 0
        while True:
            # Lấy tin nhắn tiếp theo
            line = MESSAGES[current_index]
            print(f"\nTin nhắn tiếp theo ({current_index + 1}/{len(MESSAGES)}):")
            print(line)
            
            # Đợi người dùng nhấn Enter
            user_input = input("Nhấn Enter để gửi tin nhắn (q để dừng)...").strip().lower()
            if user_input in {"q", "quit", "exit"}:
                break
            if user_input != "":
                continue
            
            # Gửi tin nhắn
            send_message_line(bus, line)
            time.sleep(0.5)
            
            # Chuyển đến tin nhắn tiếp theo
            current_index = (current_index + 1) % len(MESSAGES)
            
    except KeyboardInterrupt:
        print("\nĐã dừng phát lại")
    finally:
        bus.shutdown()

if __name__ == "__main__":
    main()

import socket
import argparse
import sys
from struct import pack

DEFAULT_PORT = 69
BLOCK_SIZE = 512
DEFAULT_TRANSFER_MODE = 'octet'

OPCODE = {'RRQ': 1, 'WRQ': 2, 'DATA': 3, 'ACK': 4, 'ERROR': 5}
MODE = {'netascii': 1, 'octet': 2, 'mail': 3}

ERROR_CODE = {
    0: "정의되지 않음, 오류 메시지 참조 (있는 경우).",
    1: "파일을 찾을 수 없음.",
    2: "접근 권한 오류.",
    3: "디스크가 가득 찼거나 할당 초과.",
    4: "잘못된 TFTP 작업.",
    5: "알 수 없는 전송 ID.",
    6: "파일이 이미 존재합니다.",
    7: "사용자가 없습니다."
}

def send_rrq(filename, mode):
    format = f'>h{len(filename)}sB{len(mode)}sB'
    rrq_message = pack(format, OPCODE['RRQ'], bytes(filename, 'utf-8'), 0, bytes(mode, 'utf-8'), 0)
    sock.sendto(rrq_message, server_address)

def send_ack(seq_num, server):
    format = f'>hh'
    ack_message = pack(format, OPCODE['ACK'], seq_num)
    sock.sendto(ack_message, server)

def send_wrq(filename, mode):
    format = f'>h{len(filename)}sB{len(mode)}sB'
    wrq_message = pack(format, OPCODE['WRQ'], bytes(filename, 'utf-8'), 0, bytes(mode, 'utf-8'), 0)

    # 타임아웃 설정 (예: 5초)
    sock.settimeout(5)

    try:
        sock.sendto(wrq_message, server_address)

        # 서버로부터 응답 수신
        data, server_new_socket = sock.recvfrom(516)
        opcode = int.from_bytes(data[:2], 'big')

        if opcode == OPCODE['ACK']:
            print("File upload started successfully.")
        elif opcode == OPCODE['ERROR']:
            error_code = int.from_bytes(data[2:4], byteorder='big')
            print(ERROR_CODE[error_code])
            sys.exit(1)
        else:
            print("Unexpected response from the server.")
            sys.exit(1)

    except socket.timeout:
        print("Timeout: Unable to establish connection with the server.")
        sock.close()
        sys.exit(1)  # 또는 다른 조치를 취할 수 있습니다.
    except Exception as e:
        print(f"Error during WRQ: {str(e)}")
        sys.exit(1)

def send_data(filename, mode, expected_block_number):
    # 서버에서 데이터를 저장할 동일한 이름의 파일 열기
    file = open(filename, 'ab')  # 'ab' 모드로 변경하여 이진 쓰기 모드로 파일을 열도록 수정

    # 파일 데이터 읽기
    file_data = file.read(BLOCK_SIZE)

    while file_data:
        print(f"Read {len(file_data)} bytes from file: {file_data}")

        # DATA 메시지를 생성하고 서버에 전송
        format = f'>hh{len(file_data)}s'
        data_message = pack(format, OPCODE['DATA'], expected_block_number, file_data)
        sock.sendto(data_message, server_address)

        # ACK 메시지를 기다리고 수신
        try:
            data, server_new_socket = sock.recvfrom(516)
            opcode = int.from_bytes(data[:2], 'big')

            if opcode == OPCODE['ACK']:
                ack_block_number = int.from_bytes(data[2:4], 'big')
                print(f"Received ACK for block {ack_block_number}")
                expected_block_number += 1
            elif opcode == OPCODE['ERROR']:
                error_code = int.from_bytes(data[2:4], byteorder='big')
                print(ERROR_CODE[error_code])
                break
            else:
                print("Unexpected response from the server.")
                break

        except socket.timeout:
            print("Timeout: Unable to receive acknowledgment from the server.")
            sock.close()
            sys.exit(1)

        # 파일 데이터 다음 블록 읽기
        file_data = file.read(BLOCK_SIZE)

    # 파일 전송이 완료되면 파일 닫기
    file.close()

# 명령행 인수 파싱
parser = argparse.ArgumentParser(description='TFTP client program')
parser.add_argument(dest="host", help="Server IP address", type=str)
parser.add_argument(dest="operation", help="get or put a file", type=str)
parser.add_argument(dest="filename", help="name of file to transfer", type=str)
parser.add_argument("-p", "--port", dest="port", type=int, default=DEFAULT_PORT)
args = parser.parse_args()

# UDP 소켓 생성
server_ip = args.host
server_port = args.port
server_address = (server_ip, server_port)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 기본 설정
mode = DEFAULT_TRANSFER_MODE
operation = args.operation
filename = args.filename

# RRQ_message 또는 WRQ_message 전송
if operation.lower() == 'get':
    send_rrq(filename, mode)
elif operation.lower() == 'put':
    send_wrq(filename, mode)
else:
    print("Invalid operation. Use 'get' or 'put'.")
    sys.exit(1)

# 서버에서 데이터를 저장할 동일한 이름의 파일 열기
file = open(filename, 'wb')
expected_block_number = 1

while True:
    data, server_new_socket = sock.recvfrom(516)
    opcode = int.from_bytes(data[:2], 'big')

    if opcode == OPCODE['DATA']:
        print(f"Received DATA message")

        block_number = int.from_bytes(data[2:4], 'big')
        if block_number == expected_block_number:
            send_ack(block_number, server_new_socket)
            file_block = data[4:]
            file.write(file_block)
            expected_block_number = expected_block_number + 1
            print(file_block.decode())
        else:
            send_ack(expected_block_number - 1, server_new_socket)

    elif opcode == OPCODE['ERROR']:
        error_code = int.from_bytes(data[2:4], byteorder='big')
        if error_code == 1:
            print("서버에서 요청한 파일을 찾을 수 없습니다.")
            break
        else:
            print(ERROR_CODE[error_code])
            break

    else:
        break

    if len(file_block) < BLOCK_SIZE:
        file.close()
        print(len(file_block))
        break

# $ tftp ip_address [-p port_mumber] <get|put> filename

import socket
import argparse
import sys
import time  # 타임아웃 처리를 위해 time 모듈 추가
from struct import pack  # pack을 사용하지 않는 경우 주석 처리

DEFAULT_PORT = 69  # 기본 포트
BLOCK_SIZE = 512  # 블록 크기
DEFAULT_TRANSFER_MODE = 'octet'  # 기본 전송 모드

OPCODE = {'RRQ': 1, 'WRQ': 2, 'DATA': 3, 'ACK': 4, 'ERROR': 5}  # TFTP 오퍼레이션 코드
MODE = {'netascii': 1, 'octet': 2, 'mail': 3}  # 전송 모드

ERROR_CODE = {
    0: "정의되지 않음, 오류 메시지 참조 (있는 경우).",
    1: "파일을 찾을 수 없음.",
    2: "액세스 거부.",
    3: "디스크 가득 참 또는 할당 초과.",
    4: "잘못된 TFTP 작업.",
    5: "알 수 없는 전송 ID.",
    6: "파일이 이미 존재함.",
    7: "해당하는 사용자가 없음."
}


def send_wrq(filename, mode, server_address):
    # WRQ 패킷을 생성하고 서버로 전송
    format = f'>h{len(filename)}sB{len(mode)}sB'
    wrq_message = pack(format, OPCODE['WRQ'], bytes(filename, 'utf-8'), 0, bytes(mode, 'utf-8'), 0)
    sock.sendto(wrq_message, server_address)
    print("send wrq")


def send_rrq(filename, mode, server_address):
    # RRQ 패킷을 생성하고 서버로 전송
    format = f'>h{len(filename)}sB{len(mode)}sB'
    rrq_message = pack(format, OPCODE['RRQ'], bytes(filename, 'utf-8'), 0, bytes(mode, 'utf-8'), 0)
    sock.sendto(rrq_message, server_address)
    print("send rrq")


def send_ack(seq_num, server):
    # ACK 패킷을 생성하고 서버로 전송
    format = f'>hh'
    ack_message = pack(format, OPCODE['ACK'], seq_num)
    sock.sendto(ack_message, server)
    print("send ack")


def send_data(seq_num, server, data):
    # DATA 패킷을 생성하고 서버로 전송
    format = f'>hh{len(data)}s'
    data_message = pack(format, OPCODE['DATA'], seq_num, data)
    sock.sendto(data_message, server)
    print("send data")


def receive_file():
    # 서버로부터 파일을 수신하는 함수
    file = open(filename, "wb")
    # 수신한 데이터를 이진 쓰기 모드
    seq_number = 0
    # 데이터 블록의 시퀀스 번호를 초기화

    while True:
        # 서버로부터 데이터 수신
        data, server = sock.recvfrom(516)
        opcode = int.from_bytes(data[:2], 'big')
        # 수신한 데이터의 처음 2바이트를 읽어 오퍼레이션 코드 확인

        if opcode == OPCODE['DATA']:
            # 받은 데이터가 DATA 패킷인 경우
            seq_number = int.from_bytes(data[2:4], 'big')
            send_ack(seq_number, server)
            file_block = data[4:]
            # 데이터 블록 읽어 오기
            file.write(file_block)
            # 읽어온 데이터 블록을 파일에 씀

            if len(file_block) < BLOCK_SIZE:
                file.close()
                # 데이터 블록이 TFTP 블록 크기 보다 작으면 종료
                break

        elif opcode == OPCODE['ERROR']:
            # 받은 데이터가 ERROR 패킷인 경우
            error_code = int.from_bytes(data[2:4], byteorder='big')
            print(ERROR_CODE[error_code])
            break

        else:
            # 다른 오퍼레이션 코드가 오면 종료
            break

        file_block = data[4:]
        print(file_block.decode())
        # 받아온거 print로 보여주기
        
        file.write(file_block)
        if len(file_block) < BLOCK_SIZE:
            # 마지막 데이터 블록이면
            file.close()
            # 파일 종료
            break


def send_file():
    # 파일을 서버로 전송하는 함수
    try:
        file_send = open(filename, "rb")
        # 이진 읽기 모드

        while True:
            data, server = sock.recvfrom(4)
            # 헤더크기 만큼 받아오기
            opcode = int.from_bytes(data[:2], 'big')

            if opcode == OPCODE['ACK']:
                seq_number = int.from_bytes(data[2:4], 'big') + 1
                contents = file_send.read(512)
                #파일에서 512씩 읽어옴

                if not contents:
                    send_data(seq_number, server, b'')
                    # 빈 내용 이면
                    break

            send_data(seq_number, server, contents)

            if len(contents) < BLOCK_SIZE:
                file_send.close()
                break

            # 타임아웃 설정
            sock.settimeout(5)  # 5초 타임아웃

            try:
                # ACK를 기다림
                data, server = sock.recvfrom(4)
                opcode = int.from_bytes(data[:2], 'big')

                if opcode == OPCODE['ACK']:
                    seq_number = int.from_bytes(data[2:4], 'big') + 1

                else:
                    print("ACK 수신 오류")
                    break

            except socket.timeout:
                # 타임아웃 발생 시 다시 데이터 전송
                print("타임아웃 발생. 데이터 재전송 중...")
                file_send.seek(-len(contents), 1)  # 파일 포인터를 이전 위치로 이동
                continue

    except FileNotFoundError:
        print("파일을 찾을 수 없습니다.")
        sys.exit(1)


# 명령 줄 인수 구문 분석
parser = argparse.ArgumentParser(description='TFTP 클라이언트 프로그램')
parser.add_argument(dest="host", help="서버 IP 주소", type=str)
parser.add_argument(dest="action", help="파일 가져오기 또는 전송", type=str)
parser.add_argument(dest="filename", help="전송할 파일의 이름", type=str)
parser.add_argument("-p", "--port", dest="port", action="store", type=int)

args = parser.parse_args()

# Create a UDP socket

server_ip = args.host
server_port = DEFAULT_PORT

if args.port is not None:
    # 명령어 칠 때 --port 옵션을 쓰면 포트 바꿔 주기
    server_port = args.port

server_address = (server_ip, server_port)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

mode = DEFAULT_TRANSFER_MODE
filename = args.filename

if args.action == 'get':
    send_rrq(filename, mode, server_address)
    receive_file()
    print("성공~!")
elif args.action == 'put':
    send_wrq(filename, mode, server_address)
    send_file()
    print("성공~!")
else:
    print("명령어를 수정해주세요")

sock.close()

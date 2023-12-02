TFTP 클라이언트

개요
이 TFTP 클라이언트는 Trivial File Transfer Protocol (TFTP)를 사용하여 파일을 서버로 전송하거나 서버로부터 파일을 가져오는 기능을 제공합니다.

기능
파일 가져오기 (get): 서버로부터 파일을 다운로드합니다.
파일 전송하기 (put): 파일을 서버로 업로드합니다.
포트 설정 기능: (서버포트가 69번이 아닐 경우에 사용하기 위함)
파일 오류처리: 요청한 파일이 서버에 없을 경우 사용자에게 알리고 종료

요구 사항
Python 3.x
소켓 및 argparse 모듈

사용법

설치
# 깃 리포지토리를 클론합니다.
git clone https://github.com/yourusername/tftp-client.git
# 프로젝트 폴더로 이동합니다.
cd tftp-client
명령어 구문
$ tftp ip_address [-p port_number] <get|put> filename
명령어 예제
파일 가져오기 (get):
$ python tftp_client.py 192.168.1.100 get example.txt
파일 전송하기 (put):
$ python tftp_client.py 192.168.1.100 put example.txt
ip_address: TFTP 서버의 IP 주소
-p port_number: (선택 사항) TFTP 서버의 포트 번호. 지정하지 않으면 기본 포트 69를 사용합니다.
<get|put>: 가져오기 또는 전송 명령 중 하나를 선택합니다.
filename: 전송하거나 가져올 파일의 이름.

예외 상황
파일을 찾을 수 없음
액세스 거부
디스크 가득 참 또는 할당 초과
잘못된 TFTP 작업
알 수 없는 전송 ID
파일이 이미 존재함
해당하는 사용자가 없음
get:중복된 데이터블록 수신 처리
put:전송한 데이터블록에 대한 타임아웃

주의 사항
이 클라이언트는 UDP 소켓을 사용하므로, 네트워크 연결이 안정적인 환경에서 사용하세요.
파일 전송이나 가져오기 중 오류가 발생하면 해당 오류 메시지가 표시됩니다.

라이센스
이 소프트웨어는 MIT 라이센스를 따릅니다. 자세한 내용은 LICENSE.md 파일을 참조하세요.


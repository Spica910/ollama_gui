import subprocess
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
import webbrowser
import logging

# Flask 애플리케이션 생성 및 SocketIO 초기화
app = Flask(__name__)
socketio = SocketIO(app)

# 로깅 설정 (콘솔에 로그 기록)
logging.basicConfig(level=logging.INFO)

def run_llama_conversation(prompt):
    """
    Ollama를 이용하여 로컬에 설치된 LLaMA 3.2 모델을 실행하고 대화의 응답을 반환합니다.
    """
    try:
        logging.info(f"LLaMA 명령 실행 중... 사용자 입력: {prompt}")
        result = subprocess.run(
            ['ollama', 'run', 'llama3.2:latest'],
            input=prompt,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60  # 실행 시간 제한 설정
        )
        if result.returncode == 0:
            logging.info(f"LLaMA 응답: {result.stdout.strip()}")
            return result.stdout.strip()
        else:
            logging.error(f"Error: {result.stderr}")
            return f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        logging.error("LLaMA 명령 실행 시간 초과.")
        return "Error: LLaMA 명령 실행 시간 초과."
    except Exception as e:
        logging.error(f"Exception occurred: {str(e)}")
        return f"Exception occurred: {str(e)}"

def emit_typing_effect(response, delay=50):
    """
    LLaMA의 응답을 한 글자씩 실시간으로 클라이언트에 전송하는 함수
    """
    logging.info(f"LLaMA 응답 타이핑 효과 시작: {response}")
    for char in response:
        emit('server_typing', {'message': char, 'sender': 'LLaMA'}, broadcast=True)
        socketio.sleep(delay / 1000.0)  # 밀리초 단위 지연
    logging.info("타이핑 효과 완료")

@app.route('/')
def index():
    return render_template('chat.html')

@socketio.on('user_message')
def handle_user_message(data):
    user_input = data['message']
    
    # 사용자 메시지 클라이언트에 전송
    logging.info(f"사용자 입력: {user_input}")
    emit('server_message', {'message': user_input, 'sender': 'You'}, broadcast=True)
    
    # LLaMA 모델 실행
    response = run_llama_conversation(user_input)
    
    # LLaMA 응답을 실시간으로 한 글자씩 전송
    emit_typing_effect(response)
    
    # LLaMA 응답이 끝났음을 클라이언트에 알림
    emit('server_typing_end', {}, broadcast=True)

def open_browser():
    """
    Flask 애플리케이션이 시작될 때 웹 브라우저를 자동으로 엽니다.
    """
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == "__main__":
    # 웹 브라우저를 자동으로 여는 쓰레드 시작
    threading.Timer(1, open_browser).start()
    
    # Flask 애플리케이션 실행
    socketio.run(app, debug=False)
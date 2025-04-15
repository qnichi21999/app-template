import os
import subprocess

def start_app():
    subprocess.Popen(['uvicorn', 'consumer.main:app', '--host', '0.0.0.0', '--port', '8080', '--reload'])
    os.system('python /app/consumer/consume.py')

if __name__ == "__main__":
    start_app()
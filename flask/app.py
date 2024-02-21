from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import paramiko
from paramiko.ssh_exception import NoValidConnectionsError, SSHException
from threading import Lock

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_strong_secret_key'
socketio = SocketIO(app)

ssh_client = None
ssh_lock = Lock()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        hostname = request.form['hostname']
        username = request.form['username']
        key_path = request.form['key_path']
        port = int(request.form.get('port', 22))
        try:
            connect_ssh(hostname, username, key_path, port)
            return render_template('index.html')
        except Exception as e:
            return render_template('index.html', error=str(e))
    return render_template('index.html')

def connect_ssh(hostname, username, key_path, port):
    global ssh_client
    key = paramiko.RSAKey.from_private_key_file(key_path)
    with ssh_lock:
        if ssh_client and ssh_client.get_transport().is_active():
            ssh_client.close()
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=hostname, username=username, pkey=key, port=port)

def listen_to_ssh(socketio, command):
    global ssh_client
    try:
        with ssh_lock:
            if ssh_client and ssh_client.get_transport().is_active():
                ssh_shell = ssh_client.invoke_shell()
                stdin, stdout, stderr = ssh_shell.exec_command(command)
                for line in stdout:
                    output = line.decode('utf-8').strip()
                    socketio.emit('ssh_response', {'data': output}, namespace='/ssh')
            else:
                socketio.emit('ssh_response', {'data': 'SSH connection is not active.'}, namespace='/ssh')
    except SSHException as e:
        socketio.emit('ssh_response', {'data': f'Error: {str(e)}'}, namespace='/ssh')

@socketio.on('connect', namespace='/ssh')
def ssh_connect():
    emit('ssh_response', {'data': 'Connected to SSH WebSocket'})

@socketio.on('disconnect', namespace='/ssh')
def ssh_disconnect():
    global ssh_client
    with ssh_lock:
        if ssh_client:
            ssh_client.close()

@socketio.on('ssh_command', namespace='/ssh')
def handle_ssh_command(command):
    socketio.start_background_task(listen_to_ssh, socketio, command['data'])

@socketio.on('start_ssh', namespace='/ssh')
def start_ssh(data):
    global ssh_client
    try:
        with ssh_lock:
            if ssh_client and ssh_client.get_transport().is_active():
                emit('ssh_response', {'data': 'SSH connection is already active.'})
            else:
                connect_ssh(data['hostname'], data['username'], data['key_path'], data['port'])
                emit('ssh_response', {'data': 'SSH connection established.'})
    except NoValidConnectionsError as e:
        emit('ssh_response', {'data': str(e)})

if __name__ == '__main__':
    socketio.run(app, debug=True)

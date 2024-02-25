from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
import paramiko

app = Flask(__name__)
socketio = SocketIO(app)

# Replace the following dictionary with your server information
servers = {
    'Server1': {'hostname': 'localhost', 'username': 'bh289', 'password': 'g98vpr9v'},
    'Server2': {'hostname': 'server2.example.com', 'username': 'your_username', 'password': 'your_password'},
    # Add more servers as needed
}


@app.route('/')
def index():
    return render_template('index.html', servers=servers)

@app.route('/connect/<server_name>')
def connect(server_name):
    if server_name in servers:
        server_info = servers[server_name]
        return render_template('terminal.html', server_name=server_name, server_info=server_info)
    else:
        return "Server not found."

def ssh_thread(server_name, message):
    server_info = servers.get(server_name)
    if server_info:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(server_info['hostname'], username=server_info['username'], password=server_info['password'])
            stdin, stdout, stderr = ssh.exec_command(message)
            output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
            socketio.emit('message', {'output': output, 'server_name': server_name})
        except Exception as e:
            socketio.emit('message', {'output': f"Error executing command on {server_name}: {str(e)}", 'server_name': server_name})
        finally:
            ssh.close()

@socketio.on('connect', namespace='/ws')
def handle_connect():
    emit('message', {'output': "WebSocket connected", 'server_name': ''})

@socketio.on('execute_command', namespace='/ws')
def handle_execute_command(data):
    server_name = data['server_name']
    command = "ls"
    threading.Thread(target=ssh_thread, args=(server_name, command)).start()

if __name__ == '__main__':
    socketio.run(app, debug=True)

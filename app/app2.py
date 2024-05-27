from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import paramiko

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"
socketio = SocketIO(app)

ssh_clients = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ssh', methods=['POST'])
def ssh_connect():
    ssh_key_path = request.form['ssh_key_path']
    username = request.form['username']
    hostnames = request.form['hostname'].split(' ')  # Multiple hostnames separated by commas
    port = request.form.get('port', 22)

    session_id = request.remote_addr  # Use client IP as session ID
    ssh_clients[session_id] = []

    try:
        for hostname in hostnames:
            # Establish SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=hostname.strip(), username=username, key_filename=ssh_key_path, port=port)

            # Store SSH client in dictionary
            ssh_clients[session_id].append((hostname, ssh))
            print("connected to " +username+"@"+hostname.strip())

        return render_template('ssh.html', hostnames=hostnames, username=username, ssh_key_path=ssh_key_path, session_id=session_id)
    except paramiko.ssh_exception.AuthenticationException:
        output = "Authentication failed. Please check your credentials."
    except Exception as e:
        output = f"An error occurred: {str(e)}"

    return render_template('index.html', output=output)

@socketio.on('connect', namespace='/ssh')
def ssh_connect_socket():
    session_id = request.args.get('session_id')
    if session_id in ssh_clients:
        emit('ssh_response', {'data': 'Connected to SSH WebSocket'})
    else:
        emit('ssh_response', {'data': 'SSH session not found'})

@socketio.on('disconnect', namespace='/ssh')
def ssh_disconnect():
    session_id = request.args.get('session_id')
    if session_id in ssh_clients:
        ssh_list = ssh_clients.pop(session_id)
        for hostname, ssh in ssh_list:
            ssh.close()

@socketio.on('ssh_command', namespace='/ssh')
def handle_ssh_command(command):
    session_id = request.args.get('session_id')
    if session_id in ssh_clients:
        responses = []
        for hostname, ssh in ssh_clients[session_id]:
            stdin, stdout, stderr = ssh.exec_command(command['data'])
            output = stdout.read().decode()
            responses.append(f"{hostname}:\n{output}")

        emit('ssh_response', {'data': "\n".join(responses)})
    else:
        emit('ssh_response', {'data': 'SSH session not found'})

if __name__ == '__main__':
    socketio.run(app, debug=True)


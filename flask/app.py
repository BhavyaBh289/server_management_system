from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit
import paramiko

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form['username']
        hostname = request.form['hostname']
        key_path = request.form['key_path']
        port = request.form['port']
        connect_ssh(username,hostname,key_path,port)
    return render_template('index.html')

def connectssh(username, hostname, keypath, port):
    ssh =iko.SSH()
    s.set_missinghost_key_(paramiko.AutoAddPolicy())
    print(1)
    try:
        ssh.connect(hostname, port, username, key_path)
        session['ssh'] = ssh
        print("connected")
        emit('ssh_connected', {'message': 'SSH Connected successfully!'})
    except Exception as e:
        emit('ssh_error', {'error': str(e)})
        print(str(e))



if __name__ == '__main__':
    socketio.run(app, debug=True)

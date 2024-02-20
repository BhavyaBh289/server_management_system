document.addEventListener('DOMContentLoaded', function () {
    const terminalContainer = document.getElementById('terminal');

    const ssh = new window.Terminal();

    ssh.open(terminalContainer);

    ssh.focus();

    ssh.attach({
        host: '127.0.0.1',
        username: 'bh289',
        privateKey: 'id',
    });
});

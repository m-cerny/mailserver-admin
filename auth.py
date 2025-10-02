from nicegui import ui, app
from passlib.hash import sha512_crypt

# Authentication class
class Authentification:
    def __init__(self):
        pass

    @staticmethod
    def load_users(filename='mailserver/postfix-accounts.cf'):
        """Load users from a file."""
        users = {}
        try:
            with open(filename, 'r') as f:
                for line in f:
                    username, password_hash = line.strip().split('|{SHA512-CRYPT}')
                    users[username] = password_hash
        except FileNotFoundError:
            ui.notify("Users file not found", color='negative')
        return users

    @staticmethod
    def logout() -> None:
        """Logout the user."""
        app.storage.user.clear()
        ui.navigate.to('/login')

    @staticmethod
    def auth(username, pswd):
        """Authenticate user."""
        users = Authentification.load_users()
        if username in users:
            return sha512_crypt.verify(pswd, users[username])
        return False
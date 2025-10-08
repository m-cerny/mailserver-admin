from nicegui import ui, app
from passlib.hash import sha512_crypt
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import RedirectResponse
from fastapi import Request

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Ignore NiceGUI static files
        if path.startswith('/_nicegui'):
            return await call_next(request)

        # Ignore unrestricted pages
        unrestricted_page_routes = {'/login', '/admin/login'}
        if path in unrestricted_page_routes:
            return await call_next(request)

        # Redirect if not authenticated
        if not app.storage.user.get('authenticated', False):
            redirect_path = path if path not in unrestricted_page_routes else '/'
            return RedirectResponse(f'/login?redirect_to={redirect_path}')

        return await call_next(request)
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
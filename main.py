# Standard imports
from typing import Optional
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

# NiceGUI components
from nicegui import app, ui

# Local modules
from user import User
from admin import Admin
from auth import Authentification
# from config import CONST

# Misc utilities
import asyncio, os

"""
todo:

"""
title = os.getenv("SITE_TITLE")
# Paths that don't require authentication
# unrestricted_page_routes = {'admin/login'}


# ----------------- Middleware for Access Control -----------------

# class AuthMiddleware(BaseHTTPMiddleware):
#     """Middleware to restrict access to authenticated users only."""

#     async def dispatch(self, request: Request, call_next):
#         # If not authenticated and trying to access protected route
#         if not app.storage.user.get('authenticated', False):
#             if not request.url.path.startswith('/_nicegui') and request.url.path not in unrestricted_page_routes:
#                 # Redirect to login with original destination saved
#                 return RedirectResponse(f'admin/login?redirect_to={request.url.path}')
#         return await call_next(request)

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



# Register the middleware
app.add_middleware(AuthMiddleware)


# ----------------- Header UI (appears on all pages) -----------------

def header():
    username = app.storage.user.get('username')
    actual_user = User(username)
    with ui.header(elevated=True).style('background-color: #000000').classes('items-center justify-between'):
        ui.link(title, "/").classes('text-2xl')  # Logo/Home link
        with ui.card().classes('bg-blue-500 text-white'):
            ui.label(f'You are logged as: {actual_user.name}')
            if actual_user.is_admin():
                ui.label(f'You have administrator privilege')
        with ui.column():
            ui.link('Admin', "/dashboard")
            ui.button(on_click=Authentification.logout, icon='logout').props('outline round')


# ----------------- Main User Page -----------------
@ui.page('/')
def main_page():
    # ui.element('div')
    header()
    

    username = app.storage.user.get('username')
    print(username)
    if username:
        current_user = User(name=username)
        def update_table():
            current_user.init()
            rows = [{"email": current_user.name, 
                        "aliases": str(current_user.aliases), 
                        "quota": current_user.quota,
                        "usage (MB)": current_user.usage,
                        "usage (%)": current_user.usage_percent
                        }]
            return rows
        with ui.row().style('display:flex; justify-content:center; gap:20px; width:100%'):
            with ui.grid(columns=1).classes('items-center justify-center '):
                overview = ui.table(columns=[{"email":"email","label":"EMAIL","field":"email", },
                                            {"aliases":"aliases","label":"ALIASES","field":"aliases","style":"text-align:center; white-space:normal; word-break:break-word; min-width:200px"},
                                            {"quota":"quota","label":"QUOTAS","field":"quota"},
                                            {"usage (MB)":"usage (MB)","label":"USAGE (MB)","field":"usage (MB)"},
                                            {"usage (%)":"usage (%)","label":"USAGE (%)","field":"usage (%)"}
                                            ],
                    rows=update_table()).classes('wrap-cells w-full')

                # Password change card
                with ui.dialog() as pswd:
                    with ui.card():
                        new_password = ui.input('Password', password=True, password_toggle_button=True,
                                                validation={'Too short': lambda value: len(value) > 5})
                        ui.button('Confirm', on_click=lambda e: current_user.setup("pswd_change", new_pswd=new_password.value), color="red")
            
                
            
                
                # Buttons 
                with ui.grid(columns=2).classes(''):
                    ui.button("Password change", on_click=lambda: pswd.open()).classes('w-full')
                    with ui.grid(columns=1):
                        # Alias management card
                        with ui.dialog() as aliases_add:
                            # Add alias
                            with ui.card():
                                add_alias_ = ui.input('Adress', password=False,
                                                    validation={'wrong format!': lambda value: User.is_valid_email(value)})

                                def click_handle():
                                    current_user.setup("add_alias", alias=add_alias_.value)
                                    overview.update_rows(rows=update_table())
                                    aliases_add.close()

                                ui.button('Confirm', on_click=click_handle)

                        with ui.dialog() as aliases_del:
                            with ui.card():
                                selected_alias = []
                                def open_delete_alias():
                                    current_user.init()
                                    alias_select.set_options(current_user.aliases)
                                    aliases_del.open()

                                def selection_handle(e):
                                    selected_alias.clear()
                                    selected_alias.append(e.value)

                                def click_handle_del():

                                    if selected_alias:
                                        current_user.setup("del_alias", alias=selected_alias[-1])
                                        overview.update_rows(rows=update_table())
                                        aliases_del.close()

                                alias_select = ui.select([], multiple=False, on_change=selection_handle, clearable=True, with_input=True).classes('w-full')
                                ui.button('Confirm', on_click=click_handle_del)

                        ui.button("Add Alias", on_click=lambda: aliases_add.open()).classes('w-full')
                        ui.button("Delete Alias", on_click=open_delete_alias).classes('w-full')

    else:
        # No user in storage? Force logout
        Authentification.logout()


# ----------------- Admin Page -----------------

@ui.page('/dashboard')
def admin_page():
    user_data = app.storage.user.get('username')
    if user_data:
        current_user = User(user_data)

        if current_user.is_admin():
            users = Admin.email("list")
            quota_users = Admin.quota_users(Admin.overview())
            nonquota_users = list(set(users) - set(quota_users))
            header()

            with ui.grid():
                # Users overview card
                overview = ui.table(
                        # columns=[
                        #     {"name": "email", "label": "Email", "field": "email"},
                        #     {"name": "used", "label": "Used", "field": "used"},
                        #     {"name": "quota", "label": "Quota", "field": "quota"},
                        #     {"name": "percent_used", "label": "% Used", "field": "percent_used"},
                        #     {"name": "aliases", "label": "Aliases", "field": "aliases"},
                        # ],
                        rows=Admin.table_data(Admin.overview())
                        )

                # User management card
                with ui.dialog() as add_user:

                    # Add user
                    with ui.card():
                        async def click_handle_add(username_, password_):
                            if User.is_valid_email(username_):
                                Admin.email("add", username_, password_)
                                # print(Admin.table_data(Admin.overview()))
                                await asyncio.sleep(2) 
                                # print(Admin.table_data(Admin.overview()))
                                overview.update_rows(rows=Admin.table_data(Admin.overview()))
                                add_user.close()    

                            else:
                                ui.notify("Wrong email address!", type="negative")

                        ui.label("Add a new user:")
                        username = ui.input('Username', password=False,
                                            validation={'wrong format!': lambda value: User.is_valid_email(value)})
                        password = ui.input('Password', password=True, password_toggle_button=True).on(
                            'keydown.enter', lambda e: click_handle_add(username.value, password.value))
                        ui.button('Confirm', on_click=lambda e: click_handle_add(username.value, password.value))
                
                # with ui.dialog() as del_user:
                #     # Delete user
                #     with ui.card():
                #         selected_user_del = None  # jen jeden uživatel

                #         def selection_handle(e):
                #             nonlocal selected_user_del
                #             selected_user_del = e.value

                #         async def click_handle_del():
                #             if selected_user_del:
                #                 Admin.email("del", address=[selected_user_del])
                #                 await asyncio.sleep(1)  # krátká pauza pro backend
                #                 overview.update_rows(rows=Admin.table_data(Admin.overview()))
                #                 del_user.close()

                #         ui.label("Delete user:")
                #         del_select = ui.select(users, multiple=False, on_change=selection_handle, clearable=True)

                #         # async callback předáme přímo, bez lambda
                #         ui.button('Confirm', on_click=click_handle_del)

                with ui.dialog() as del_user:
                    # Delete user
                    with ui.card():
                        selected_users_del = []

                        def selection_handle(e):
                            selected_users_del.clear()
                            del_select.set_options(Admin.email("list"))
                            selected_users_del.append(e.value)

                        async def click_handle_del(selected_users_del):
                            Admin.email("del", address=selected_users_del)
                            await asyncio.sleep(1)
                            overview.update_rows(rows=Admin.table_data(Admin.overview()))
                            del_user.close()

                        ui.label("Delete user:")
                        del_select =ui.select(users, multiple=False, on_change=selection_handle, clearable=True)
                        ui.button('Confirm', on_click=lambda e: click_handle_del(selected_users_del))

                # Quota management card
                with ui.dialog() as set_quota:

                    # Set quota
                    with ui.card():
                        sel_nonquota_users = []
                        def sel_handle_quota_set(e):
                            sel_nonquota_users.append(e.value)

                        async def click_handle_quota_set(sel_nonquota_users):
                            Admin.quota("set", address=sel_nonquota_users, quota=slider.value)
                            await asyncio.sleep(3)
                            ui.navigate.to("/dashboard")
                        ui.label("Set quota to user:")
                        with ui.card_section():
                            ui.select(nonquota_users, multiple=False, on_change=sel_handle_quota_set, clearable=True)
                        with ui.card_section():
                            with ui.row():
                                ui.label("Size (MiB):")
                                slider=ui.slider(min=100, max=5000, value=500, step=100)
                                ui.label().bind_text_from(slider, 'value')
                        ui.button('Confirm', on_click=lambda e: click_handle_quota_set(sel_nonquota_users))
                    
                with ui.dialog() as del_quota:
                    # Delete quota
                    with ui.card():
                        sel_users_quota = []

                        def sel_handle_quota_del(e):
                            sel_users_quota.append(e.value)

                        async def click_handle_quota_del(sel_users_quota):
                            Admin.quota("del", address=sel_users_quota)
                            await asyncio.sleep(3)
                            ui.navigate.to("/dashboard")

                        ui.label("Delete user's quota:")
                        ui.select(quota_users, multiple=False, on_change=sel_handle_quota_del, clearable=True)
                        ui.button('Confirm', on_click=lambda e: click_handle_quota_del(sel_users_quota))
                with ui.grid(columns=2):
                    with ui.grid():
                        ui.button("Add a new user", on_click=lambda: add_user.open())
                        ui.button("Delete user", on_click=lambda: del_user.open())
                    with ui.grid():
                        ui.button("Set quota", on_click=lambda: set_quota.open())
                        ui.button("Delete quota", on_click=lambda: del_quota.open())
       


        else:
            # Non-admin trying to access admin page
            header()
            ui.label("You are not an administrator!")


# ----------------- Login Page -----------------

@ui.page('/login')
def login(redirect_to: str = '/') -> Optional[RedirectResponse]:
    """Login page with optional redirection after login."""

    def try_login(username, password):
        if Authentification.auth(username, password):
            app.storage.user.update({'username': username, 'authenticated': True})
            loged_user = User(app.storage.user.get("username"))
            ui.navigate.to(redirect_to)
        else:
            ui.notify('Wrong username or password', color='negative')

    # If already authenticated, go to home
    if app.storage.user.get('authenticated', False):
        return RedirectResponse('/')

    # Login UI
    with ui.card().classes('absolute-center'):
        username = ui.input('Username').on('keydown.enter',
                                           lambda e: try_login(username.value, password.value))
        password = ui.input('Password', password=True, password_toggle_button=True).on(
            'keydown.enter', lambda e: try_login(username.value, password.value))
        ui.button('Log in', on_click=lambda e: try_login(username.value, password.value))

    return None


# ----------------- App Entry Point -----------------
ui.run(
    storage_secret="kusudASIDPOADDAF",
    dark=None,
    port=8080,
    host="0.0.0.0",
    title=title,
    language='cs'
        
    )

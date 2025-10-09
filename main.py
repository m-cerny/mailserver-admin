from typing import Optional
import asyncio, os
from fastapi.responses import RedirectResponse
from nicegui import app, ui

# Local modules
from user import User
from admin import Admin
from auth import Authentification, AuthMiddleware

"""
todo:
- async functions: wait until rc==0
"""
title = os.getenv("SITE_TITLE")

# Register the middleware
app.add_middleware(AuthMiddleware)

# ----------------- Header UI (appears on all pages) -----------------
def header(page):
    username = app.storage.user.get('username')
    actual_user = User(username)
    
    with ui.header(elevated=True).style('background-color: #000000').classes('items-center justify-between'):
        with ui.card():
            ui.label(f'You are logged as: {actual_user.name}')
            if actual_user.is_admin():
                ui.label(f'You are administrator')
        with ui.column():
            with ui.button(on_click=lambda e: ui.navigate.to("/dashboard"), icon="manage_accounts") as admin_link:
                ui.tooltip("Accounts administration")
            with ui.button(on_click=lambda e: ui.navigate.to("/"),icon="person") as home_link:
                ui.tooltip("Self administration")
            with ui.button(on_click=Authentification.logout, icon='logout'):
                ui.tooltip("Logout")
            if not actual_user.is_admin():
                admin_link.visible = False
    if page == "main_page":
        home_link.visible = False
    if page == "admin_page":
        admin_link.visible = False

# ----------------- User Page -----------------
@ui.page('/')
def main_page():
    ui.colors(
        primary="#d10808",
        secondary="#000000")
    header("main_page")

    username = app.storage.user.get('username')
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
                overview = ui.table(columns=[{"name":"email","label":"EMAIL","field":"email", },
                                            {"name":"aliases","label":"ALIASES","field":"aliases","style":"text-align:center; white-space:normal; word-break:break-word; min-width:200px"},
                                            {"name":"quota","label":"QUOTAS","field":"quota"},
                                            {"name":"usage (MB)","label":"USAGE (MB)","field":"usage (MB)"},
                                            {"name":"usage (%)","label":"USAGE (%)","field":"usage (%)"}
                                            ],
                    rows=update_table()).classes('wrap-cells w-full')

                # Password change card
                with ui.dialog() as pswd:
                    with ui.card():
                        new_password = ui.input('Password', password=True, password_toggle_button=True,
                                                validation={'Too short': lambda value: len(value) > 5})
                        ui.button('Confirm', on_click=lambda e: current_user.setup("pswd_change", new_pswd=new_password.value), color="red")
            
                # Buttons 
                with ui.grid(columns=2):
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
    ui.colors(
        primary="#d10808",
        secondary="#000000")
    user_data = app.storage.user.get('username')
    if user_data:
        current_user = User(user_data)

        if current_user.is_admin():
            header("admin_page")
            # with ui.element('div'): # wrapper for responsive table
            with ui.row().style('display:flex; justify-content:center; gap:20px; width:100%'):
                    with ui.grid(columns=1, rows=2).classes('items-center justify-center '):
                            # Users overview card         
                            with ui.table(columns=[{"name":"email","label":"EMAIL","field":"email", },
                                                {"name":"aliases","label":"ALIASES","field":"aliases","style":"text-align:center; white-space:normal; word-break:break-word; min-width:200px"},
                                                {"name":"quota","label":"QUOTAS","field":"quota"},
                                                {"name":"usage (MB)","label":"USAGE (MB)","field":"usage (MB)"},
                                                {"name":"usage (%)","label":"USAGE (%)","field":"usage (%)"},
                                                {"name":"actions","label":"ACTIONS","field":"actions"}
                                                ],
                                        rows=Admin.table_data(Admin.overview())
                                            ).classes('wrap-cells w-full') as overview:
                                overview.add_slot(f'body-cell-actions', """
                                <q-td :props="props">
                                    <q-btn @click="$parent.$emit('delete', props)" icon="delete" flat dense color="grey">
                                    <q-tooltip>Delete user</q-tooltip>
                                    </q-btn>
                                    <q-btn @click="$parent.$emit('quota', props)" icon="storage" flat dense color="grey">
                                    <q-tooltip>Quota setup</q-tooltip>
                                    </q-btn>
                                    <q-btn @click="$parent.$emit('alias', props)" icon="forward_to_inbox" flat dense color="grey">
                                    <q-tooltip>Alias setup</q-tooltip>
                                    </q-btn>
                                    <q-btn @click="$parent.$emit('password', props)" icon="key" flat dense color="grey">
                                    <q-tooltip>Change password</q-tooltip>
                                    </q-btn>
                                </q-td>
                                """)
                                overview.on('delete', lambda msg: on_action(msg, "del"))
                                overview.on('quota', lambda msg: on_action(msg, "quota"))
                                overview.on('alias', lambda msg: on_action(msg, "alias"))
                                overview.on('password', lambda msg: on_action(msg, "password"))

                            def on_action(msg, fce):
                                user = msg.args["row"]["email"]
                                if fce == "del":
                                    with ui.dialog() as del_user_dialog:
                                        with ui.card():
                                            async def click_handle_del(user):
                                                Admin.email("del", address=user)
                                                await asyncio.sleep(1)
                                                overview.update_rows(rows=Admin.table_data(Admin.overview()))
                                                del_user_dialog.close()

                                            ui.label(f"Delete user: {user}")
                                            ui.button('Confirm', on_click=lambda e: click_handle_del(user))
                                    del_user_dialog.open()
                                
                                if fce == "quota":   
                                    with ui.dialog() as set_quota_dialog:
                                        with ui.card():
                                            async def click_handle_quota_set(user):
                                                Admin.email("quota", address=user, quota=slider.value)
                                                await asyncio.sleep(3)
                                                overview.update_rows(rows=Admin.table_data(Admin.overview()))
                                                set_quota_dialog.close()
                                            
                                            def slider_change():
                                                if slider.value == 0:
                                                    slider_text.set_text("Unlimited")

                                            ui.label(f"Set quota to user: {user}")
                                            with ui.card_section().classes('w-full'):
                                                with ui.row():
                                                    ui.label("Size (MiB):")
                                                    slider=ui.slider(min=0, max=5000, value=500, step=100,on_change=lambda: slider_change())
                                                    slider_text = ui.label().bind_text_from(slider, 'value')
                                            ui.button('Confirm', on_click=lambda e: click_handle_quota_set(user))
                                    set_quota_dialog.open()

                                if fce == "alias":
                                    def get_aliases():
                                        aliases = msg.args["row"]["aliases"]
                                        return [a.strip() for a in aliases.split(",")]
                                    
                                    with ui.dialog() as alias_dialog:
                                        with ui.card():
                                            with ui.grid(columns=2, rows=1):
                                                with ui.card():
                                                    new_alias = ui.input("New alias")
                                                    async def click_handle_add_alias():
                                                        Admin.email("alias", address=user, new_alias=new_alias.value)
                                                        await asyncio.sleep(3)
                                                        overview.update_rows(rows=Admin.table_data(Admin.overview()))
                                                        # sel_alias.set_options(get_aliases())
                                                        alias_dialog.close()
                                                    # else: ui.notify("Wrong address", type="negative")
                                                    ui.button('Add', on_click=click_handle_add_alias)
                                                with ui.card():
                                                    sel_alias = ui.select(get_aliases(), label="Select alias").classes('w-full')
                                                    async def click_handle_del_alias():
                                                        Admin.email("alias", address=user, del_alias=sel_alias.value)
                                                        await asyncio.sleep(3)
                                                        overview.update_rows(rows=Admin.table_data(Admin.overview()))
                                                        # sel_alias.set_options()
                                                        alias_dialog.close()
                                                    ui.button("Delete", on_click=click_handle_del_alias)
                                                    alias_dialog.close()
                                    alias_dialog.open()

                                if fce == "password":
                                    with ui.dialog() as password_dialog:
                                        with ui.card():
                                            async def click_handle_password():
                                                Admin.email("password", address=user, pswd=new_passwod.value)
                                                await asyncio.sleep(2)
                                                password_dialog.close()
                                                
                                            new_passwod = ui.input("New password", password=True, password_toggle_button=True)
                                            ui.button('Change password', on_click=click_handle_password)
                                    password_dialog.open()

                            # User management card
                            with ui.dialog() as add_user:

                                # Add user
                                with ui.card():
                                    async def click_handle_add():
                                        if User.is_valid_email(username.value):
                                            Admin.email("add", username.value, password.value)
                                            await asyncio.sleep(3)
                                            overview.update_rows(rows=Admin.table_data(Admin.overview()))
                                            add_user.close()    

                                        else:
                                            ui.notify("Wrong email address!", type="negative")

                                    ui.label("Add a new user:")
                                    username = ui.input('Username', password=False,
                                                        validation={'wrong format!': lambda value: User.is_valid_email(value)})
                                    password = ui.input('Password', password=True, password_toggle_button=True)
                                    ui.button('Confirm', on_click=click_handle_add)

                            ui.button("Add a new user", on_click=lambda: add_user.open())

        else:
            # Non-admin trying to access admin page
            header()
            ui.label("You are not an administrator!")


# ----------------- Login Page -----------------
@ui.page('/login')
def login(redirect_to: str = '/') -> Optional[RedirectResponse]:
    """Login page with optional redirection after login."""
    ui.colors(
        primary="#d10808",
        secondary="#000000")

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
    language='cs')

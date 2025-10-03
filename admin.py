from nicegui import ui
import re
from user import process

class Admin:

    def __init__(self):
        pass
    @staticmethod
    def overview():
        raw_data = process("email", "list")
        if raw_data["rc"] == 0:
            # Pattern to match email blocks
            email_block_pattern = re.compile(
                r"\* (?P<email>\S+) \(\s*(?P<used>\S+)\s*/\s*(?P<quota>\S+)\s*\) \[(?P<percent>\d+)%\](?:\s*\[\s*aliases\s*->\s*(?P<aliases>[^\]]+)\])?",
                re.MULTILINE
            )

            # Parse data
            emails_info = []

            for match in email_block_pattern.finditer(raw_data["stdout"]):
                data = match.groupdict()
                emails_info.append({
                    "email": data["email"],
                    "used": data["used"],
                    "quota": data["quota"],
                    "percent_used": int(data["percent"]),
                    "aliases": [a.strip() for a in data["aliases"].split(",")] if data["aliases"] else []
                })
            return emails_info
    @staticmethod
    def table_data(data):
        for row in data:
            row['aliases'] = ', '.join(row['aliases']) if isinstance(row['aliases'], list) else ''
            if row['quota'] == '~':
                row['quota'] = 'No quota'
        return data
    
    @staticmethod
    def email(fc, address=None, pswd=None):
        
        if fc == "add" and address and len(pswd) >= 6:
            output = process("email", fc, address, pswd)
            if output["rc"] == 0:
                    ui.notify("A New user added", type='positive')
            else: ui.notify("Something wrong", type='negative')


        elif fc == "list":
            output = process("email", fc)
            if output["rc"] == 0:
                    address_list = output["stdout"]             
                    address_list =  re.findall(r'^\* ([^\s]+)', address_list, re.MULTILINE)
                    return address_list
            else: ui.notify("Something wrong", type='negative')
        
        elif fc == "del":
            address = address[-1]
            output = process("email", fc, "-y", address)
            if output["rc"] == 0:
                    ui.notify(f"User {address} deleted", type='positive')
            else: ui.notify("Something wrong", type='negative')

    @staticmethod
    def quota(fc, address, quota=None):
        if fc == "set" and quota:
            address = address[-1]
            output = process("quota", fc, address, str(quota)+"M")
            if output["rc"] == 0:
                    ui.notify(f"Quota {quota}MiB added to address: {address}", type="positive")
            else: ui.notify("Something wrong", type='negative')
        elif fc == "del" and address:
            address = address[-1]
            output = process("quota", fc, address)
            if output["rc"] == 0:
                    ui.notify(f"Quota deleted to address: {address}", type="positive")
            else: ui.notify("Something wrong", type='negative')


    @staticmethod
    def quota_users(func):
        quota_users = []
        for i in func:
             if i["quota"] != "~":
                  quota_users.append(i["email"])
        return quota_users
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
                    "usage (MB)": data["used"],
                    "quota": data["quota"],
                    "usage (%)": int(data["percent"]),
                    "aliases": [a.strip() for a in data["aliases"].split(",")] if data["aliases"] else []
                })
            return emails_info
    @staticmethod
    def table_data(data):
        for row in data:
            row["aliases"] = ", ".join(row["aliases"]) if isinstance(row["aliases"], list) else ""
            if row["quota"] == "~":
                row["quota"] = "No quota"
            # row.update({"actions": ""})
            # row.update({"select": ""})
        return data
    
    @staticmethod
    def email(fc, address=None, pswd=None, new_alias=None, del_alias=None, quota=None):

        # Add email account
        if fc == "add" and address:
            if len(pswd) > 5:
                output = process("email", fc, address, pswd)
                if output["rc"] == 0:
                        ui.notify("A New user added", type='positive')
                else: ui.notify("Password must be at least 6 characters long", type='negative')
            else: ui.notify(f"{output['stdout']}", type='negative')

        # List of emails
        elif fc == "list":
            output = process("email", fc)
            if output["rc"] == 0:
                    address_list = output["stdout"]             
                    address_list =  re.findall(r'^\* ([^\s]+)', address_list, re.MULTILINE)
                    return address_list
            else: ui.notify(f"{output['stdout']}", type='negative')

        # Delete email
        elif fc == "del" and address:
            output = process("email", fc, "-y", address)
            if output["rc"] == 0:
                    ui.notify(f"User {address} deleted", type='positive')
            else: ui.notify(f"{output['stdout']}", type='negative')

        # Quotas
        elif fc == "quota" and address:
            if quota > 0:
                fc = "set"
                output = process("quota", fc, address, str(quota)+"M")
                if output["rc"] == 0:
                        ui.notify(f"Quota {quota}MiB added to address: {address}", type="positive")
                else: ui.notify(f"{output['stdout']}", type='negative')
            elif quota == 0:
                fc = "del"
                output = process("quota", fc, address)
                if output["rc"] == 0:
                        ui.notify(f"Quota deleted to address: {address}", type="positive")
                else: ui.notify(f"{output['stdout']}", type='negative')
        
        # Aliases
        elif fc == "alias" and address:
            if address and new_alias:
                fc = "add"
                output = process("alias", fc, new_alias, address)
                if output["rc"] == 0:
                    ui.notify(f"Alias: {new_alias} added", type='positive')
                else:
                    ui.notify(f"{output['stdout']}", type='negative')

            elif address and del_alias:
                fc = "del"
                output = process("alias", fc, del_alias, address)
                if output["rc"] == 0:
                    ui.notify(f"Alias: {del_alias} deleted", type='warning')

                else:
                    ui.notify(f"{output['stdout']}", type='negative')
        # Password
        elif fc == "password" and address and pswd:
            if len(pswd) > 5:
                    output = process("email", "update", address, pswd)
                    if output["rc"] == 0:
                        ui.notify("Password changed", type='positive')
                    else:
                        ui.notify("Something went wrong!", type='negative')
            else:
                ui.notify("Password must be at least 6 characters long", type='negative')

        # # Aliases
        # elif fc == "add_alias" and address and new_alias:
        #     fc = "add"
        #     output = process("alias", fc, new_alias, address)
        #     if output["rc"] == 0:
        #         ui.notify(f"Alias: {new_alias} added", type='positive')
        #     else:
        #         ui.notify(f"{output['stdout']}", type='negative')

        # elif fc == "del_alias" and address and del_alias:
        #     fc = "del"
        #     output = process("alias", fc, del_alias, address)
        #     if output["rc"] == 0:
        #         ui.notify(f"Alias: {del_alias} deleted", type='warning')

        #     else:
        #         ui.notify(f"{output['stdout']}", type='negative')


        # if fc == "del" and name and alias:
        #     output = process("alias", fc, alias, name)
        #     if output["rc"] == 0:
        #         ui.notify(f"Alias: {alias} removed", type='positive')
        #     else:
        #         ui.notify("Something went wrong!", type='negative')

    # @staticmethod
    # def quota(fc, address, quota=None):
    #     if fc == "set_quota" and quota > 0:
    #         # address = address[-1]
    #         output = process("quota", fc, address, str(quota)+"M")
    #         if output["rc"] == 0:
    #                 ui.notify(f"Quota {quota}MiB added to address: {address}", type="positive")
    #         else: ui.notify("Something wrong", type='negative')
    #     elif fc == "set_quota" and quota == 0:
    #         fc = "del"
    #         output = process("quota", fc, address)
    #         if output["rc"] == 0:
    #                 ui.notify(f"Quota deleted to address: {address}", type="positive")
    #         else: ui.notify("Something wrong", type='negative')
             
    #     # elif fc == "del" and address:
    #     #     address = address[-1]
    #     #     output = process("quota", fc, address)
    #     #     if output["rc"] == 0:
    #     #             ui.notify(f"Quota deleted to address: {address}", type="positive")
    #     #     else: ui.notify("Something wrong", type='negative')


    @staticmethod
    def quota_users(func):
        quota_users = []
        for i in func:
             if i["quota"] != "~":
                  quota_users.append(i["email"])
        return quota_users
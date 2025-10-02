import subprocess
import re, os
from nicegui import ui
from config import CONST

# Add to conf file
admins = os.getenv("ADMINS")
admins = [e.strip() for e in admins.split(",")]
print(admins)
container_name = os.getenv("CONT_NAME")

def process(*args:str) -> dict:
    """
    keys: rc, stdout, stderr
    """
    try:
        # Running the Docker exec command
        result = subprocess.run(
            ["docker", "exec", "-it", container_name, "setup", *args], 
            check=True, 
            capture_output=True, 
            text=True  # Automatically decode stdout/stderr to string
        )

        # Prepare the output dictionary
        output = {
            "rc": result.returncode,
            "stdout": result.stdout,  # Already a string due to 'text=True'
            "stderr": result.stderr   # Capture stderr as well
        }

    except subprocess.CalledProcessError as e:
        # Handle exceptions if the command fails
        output = {
            "rc": e.returncode,
            "stdout": e.stdout if e.stdout else None,
            "stderr": e.stderr if e.stderr else None
        }

    return output


        
class User:
    
    def __init__(self, name):
        self.name = name
        self.__admin = self.is_admin()
        self.aliases = None
        self.quota = None
        self.usage = None
        self.usage_percent = None
        # self.stats = self.statistics(overview())
    
    def is_admin(self):
        """Check if the user is an admin."""
        return self.name in admins

    def statistics(self, fce):
        for item in fce:
            if item["email"] == self.name:
                return item
    
    def mailbox_size(self):
        output = process("email", "list")
        if output["rc"] == 0:
            output = output["stdout"]
            print(output)

    def init(self, user=True):
        output = process("email", "list")
        if output["rc"] == 0:
            stdout = output["stdout"]

            # Rozdělit podle hvězdiček, aby každý blok byl samostatný
            blocks = [b.strip() for b in stdout.split("* ") if b.strip()]
            result = {}

            for block in blocks:
                email_match = re.search(r'([\w\.-]+@[\w\.-]+)', block)
                email = email_match.group(1) if email_match else None

                quota_match = re.search(r'\(\s*([\d\.]+\w+)\s*/\s*([~\d\.KMG]+)\s*\)', block)
                usage = quota_match.group(1) if quota_match else None
                quota = quota_match.group(2) if quota_match else None
                if quota == "~":
                    quota = "no quota"

                aliases_match = re.search(r'aliases\s*->\s*(.+)\]', block, re.S)
                if aliases_match:
                    aliases = [a.strip() for a in aliases_match.group(1).split(",")]
                else:
                    aliases = []

                percent_match = re.search(r'\[(\d+)%\]', block)
                usage_percent = int(percent_match.group(1)) if percent_match else None

                if email:
                    result[email] = {
                        "aliases": aliases,
                        "quota": quota,
                        "usage": usage,
                        "usage_percent": usage_percent,
                    }

            print("Result keys:", list(result.keys()))
            if user == True:
                print("Looking for:", self.name)

                if self.name not in result:
                    raise ValueError(f"E-mail {self.name} nebyl nalezen.")

                self.aliases = result[self.name]["aliases"]
                self.quota = result[self.name]["quota"]
                self.usage = result[self.name]["usage"]
                self.usage_percent = result[self.name]["usage_percent"]
            if user == False:
                pass
        
    def init_quota(self):
        pass
                
    def setup (self, fc, alias=None, new_pswd=None,):

        name = self.name         

        def __alias(fc, name, alias):
            """Handle aliases."""

            if fc == "add" and name and alias:
                output = process("alias", fc, alias, name)
                if output["rc"] == 0:
                    ui.notify(f"Alias: {alias} added", type='positive')
                    self.aliases.append(alias)
                    # print(self.aliases)
                else:
                    ui.notify("Something went wrong!", type='negative')

            if fc == "del" and name and alias:
                output = process("alias", fc, alias, name)
                if output["rc"] == 0:
                    ui.notify(f"Alias: {alias} removed", type='positive')
                else:
                    ui.notify("Something went wrong!", type='negative')

        
        def __pswd_change(name, new_pswd):
            """Change password and handle system process."""
            if len(new_pswd) > 5:
                    output = process("email", "update", name, new_pswd)
                    if output["rc"] == 0:
                        ui.notify("Password changed", type='positive')
                    else:
                        ui.notify("Something went wrong!", type='negative')
            else:
                ui.notify("Password must be at least 6 characters", type='negative')
            
        
        if fc == "add_alias" and alias:
            fc = "add"
            __alias(fc, name, alias)

        elif fc == "del_alias" and alias:
            fc = "del"
            __alias(fc, name, alias)

        elif fc == "pswd_change" and new_pswd:
            __pswd_change(name, new_pswd)

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate the format of an email address."""
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(email_regex, email) is not None
#print(overview())

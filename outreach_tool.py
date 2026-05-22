import csv
import os
import time
import random
import argparse
import urllib.parse
from pathlib import Path

# Selenium Imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Config
INPUT_FILE = 'clients.csv'
TEMPLATE_FILE = 'email_template.txt'
INFLUENCER_TEMPLATE_FILE = 'influencertemplate.txt'
DRAFTS_DIR = 'drafts'
ATTACHMENT_FILE = 'presentation.pdf'  # Place your PDF attachment here

PERSONAL_DOMAINS = {
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com',
    'icloud.com', 'protonmail.com', 'me.com', 'msn.com', 'live.com', 
    'ymail.com', 'googlemail.com'
}

class OutreachTool:
    def __init__(self, args):
        self.args = args
        self.clients = []
        self.driver = None

    def run(self):
        if not self.load_data(): return
        self.templates = self.load_templates()
        if not self.templates: return

        candidates = self.get_candidates()
        if not candidates:
            print("No new emails to process.")
            return

        print(f"Processing {len(candidates)} emails...")

        self.setup_browser()
        if not self.ensure_login():
            print("Login process aborted.")
            return

        try:
            for i in candidates:
                self.process_email(i)
                self.save_csv()
                
                # Randomized safety delay between emails
                if i != candidates[-1]:
                    # Random delay between 15s and 45s (Target: Fast but Safe)
                    # To be "fast as possible" while safe, we avoid exact multiples.
                    delay = random.uniform(15, 45)
                    print(f"   [Safety] Sleeping for {int(delay)}s to avoid spam filters...")
                    time.sleep(delay)
                    
        except KeyboardInterrupt:
            print("\nStopped by user.")
        finally:
            # Persistent browser - do not quit
            if self.driver:
                print("Browser session kept open.")
                # self.driver.quit()
        
        print("Done.")

    def setup_browser(self):
        print("Launching Chrome (Selenium)...")
        options = webdriver.ChromeOptions()
        # options.add_argument("--start-maximized")
        
        # Bypass "This browser is not secure" block and improve stealth
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize standard Chrome driver (Selenium 4 manages this automatically usually)
        # Use persistent profile
        profile_dir = os.path.join(os.getcwd(), 'chrome_data')
        options.add_argument(f"user-data-dir={profile_dir}")
        options.add_experimental_option("detach", True)
        
        self.driver = webdriver.Chrome(options=options)
        
    def ensure_login(self):
        print("Navigating to Gmail...")
        self.driver.get("https://mail.google.com/")
        
        # Check if we are redirected to specific inbox or login page
        print("Checking login status...")
        try:
            # We look for a common element in the logged-in URL or title
            time.sleep(3)
            if "signin" in self.driver.current_url or "accounts.google.com" in self.driver.current_url:
                print("\n" + "!"*40)
                print("PLEASE LOG IN TO GMAIL IN THE OPENED BROWSER WINDOW.")
                print("Once you see your Inbox, press ENTER here.")
                print("!"*40 + "\n")
                input("Press Enter to continue...")
            return True
        except Exception as e:
            print(f"Browser error: {e}")
            return False

    def extract_name(self, email):
        """Extract a likely first name from an email address."""
        if not email or '@' not in email:
            return "there"
        
        local_part = email.split('@')[0]
        # Split by common separators like dot, underscore, or hyphen
        name_part = local_part.replace('_', '.').replace('-', '.').split('.')[0]
        
        # Filter out common non-names
        if name_part.lower() in ['info', 'contact', 'sales', 'support', 'hello', 'jobs', 'team']:
            return "there"
        
        # Capitalize ensuring it looks like a name (e.g., "john" -> "John")
        return name_part.capitalize()
    
    def get_attachment_path(self):
        if os.path.exists(ATTACHMENT_FILE):
             return os.path.abspath(ATTACHMENT_FILE)
        return None

    def is_personal_email(self, email):
        if not email or '@' not in email: return False
        domain = email.split('@')[1].lower().strip()
        return domain in PERSONAL_DOMAINS

    def process_email(self, idx):
        client = self.clients[idx]
        email = client.get('email', '')
        if not email: return

        # Select template
        if self.args.force_influencer or self.is_personal_email(email):
            subject, body = self.templates.get('influencer', self.templates['default'])
            template_type = "Influencer"
        else:
            subject, body = self.templates['default']
            template_type = "Default"

        # Personalization Logic
        # Try to get from CSV 'name' or 'First Name', else extract from email
        first_name = client.get('name') or client.get('First Name')
        if not first_name:
            first_name = self.extract_name(email)
        
        # Handle both placeholder types for compatibility
        personalized_body = body.replace('{First Name}', first_name).replace('{{Name}}', first_name)
        personalized_subject = subject.replace('{First Name}', first_name).replace('{{Name}}', first_name)

        print(f"[{idx+1}] Using {template_type} template for {email}")
        self.send_selenium(idx, email, personalized_subject, personalized_body)

    def send_selenium(self, idx, email, subject, body):
        print(f"      Preparing to send to: {email}")
        
        # Construct Compose URL
        params = {'view': 'cm', 'fs': '1', 'to': email, 'su': subject, 'body': body}
        url = f"https://mail.google.com/mail/?{urllib.parse.urlencode(params)}"
        
        self.driver.get(url)
        
        try:
            print("   Waiting for body...", end=" ", flush=True)
            # Randomized wait before interaction
            time.sleep(random.uniform(2, 4))
            
            wait = WebDriverWait(self.driver, 15)
            textbox = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='textbox']")))
            
            # ATTACH FILE
            attachment_path = self.get_attachment_path()
            if attachment_path:
                 print(f"   Attaching {os.path.basename(attachment_path)}...", end=" ", flush=True)
                 try:
                     # Upload file via hidden input
                     file_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='Filedata']")
                     file_input.send_keys(attachment_path)
                     # Wait for upload to complete (file size dependent)
                     time.sleep(random.uniform(20, 30)) 
                 except Exception as e:
                     print(f"   [Warning] Could not attach file: {e}")

            # Small delay to ensure text is fully populated/ready
            time.sleep(random.uniform(1, 2))
            
            # INSERT SIGNATURE (Fix for view=cm url stripping it)
            try:
                # Click the "Insert signature" pen icon
                pen_icon = self.driver.find_element(By.CSS_SELECTOR, "div[aria-label='Insert signature']")
                pen_icon.click()
                time.sleep(1)
                
                # Find the signature named "Connect"
                # Gmail signature menu items usually have role="menuitemcheckbox"
                # We look for one containing the text "Connect"
                menu_items = self.driver.find_elements(By.CSS_SELECTOR, "div[role='menuitemcheckbox']")
                found_sig = False
                for item in menu_items:
                    if "default" in item.text.lower():  # Change to match your Gmail signature name
                        item.click()
                        found_sig = True
                        print("   Signature inserted.", end=" ", flush=True)
                        break
                
                if not found_sig:
                      print("   [Info] Matching signature not found in menu.", end=" ", flush=True)

                time.sleep(1)
            except Exception as sig_e:
                print(f"   [Info] Could not auto-insert Gmail signature: {sig_e}", end=" ", flush=True)

            print("Sending...", end=" ", flush=True)
            
            cmd_key = Keys.COMMAND if "darwin" in os.sys.platform else Keys.CONTROL
            textbox.send_keys(cmd_key, Keys.ENTER)
            
            # Wait for "Message Sent" confirmation
            print("Sent.", end=" ", flush=True)
            time.sleep(random.uniform(2, 4))
            
            self.clients[idx]['status'] = 'sent'
            print("OK.")
            
        except Exception as e:
            print(f"   Failed: {e}")
            # Do NOT mark as sent

    def load_data(self):
        if not os.path.exists(INPUT_FILE):
            print("Missing clients.csv")
            return False
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.fieldnames = reader.fieldnames
            if 'status' not in self.fieldnames: self.fieldnames.append('status')
            self.clients = list(reader)
        return True

    def load_templates(self):
        templates = {}
        
        def read_tmpl(path):
            if not os.path.exists(path): return None, None
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.read().split('\n')
            
            subject = "Partnership Inquiry"
            start = 0
            if lines[0].lower().startswith("subject:"):
                subject = lines[0].split(":", 1)[1].strip()
                start = 1
                while start < len(lines) and not lines[start].strip(): start += 1
            return subject, "\n".join(lines[start:])

        # Logic: If followup, run followup for all.
        # If not followup, run default for work, influencer for personal.
        
        if self.args.followup:
            path = 'followup_template.txt'
            s, b = read_tmpl(path)
            if not b:
                print(f"Missing {path}")
                return None
            templates['default'] = (s, b)
            # Use same for influencer if doing generic followup, or you can add logic for 'influencer_followup' later
            templates['influencer'] = (s, b) 
        else:
            # Default
            s_def, b_def = read_tmpl(TEMPLATE_FILE)
            if not b_def:
                print(f"Missing {TEMPLATE_FILE}")
                return None
            templates['default'] = (s_def, b_def)

            # Influencer
            s_inf, b_inf = read_tmpl(INFLUENCER_TEMPLATE_FILE)
            if s_inf and b_inf:
                templates['influencer'] = (s_inf, b_inf)
            else:
                print(f"Warning: {INFLUENCER_TEMPLATE_FILE} missing/empty. Using default for influencers.")
                templates['influencer'] = templates['default']

        return templates

    def get_candidates(self):
        candidates = []
        for i, row in enumerate(self.clients):
            if (row.get('status') or '').lower().strip() != 'sent':
                candidates.append(i)
                if len(candidates) >= self.args.batch: break
        return candidates



    def save_csv(self):
        with open(INPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
            writer.writerows(self.clients)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', type=int, default=100)
    parser.add_argument('--followup', action='store_true')
    parser.add_argument('--force-influencer', action='store_true', help='Force using the influencer template for all emails')
    
    args = parser.parse_args()
    
    # Check for library
    if not SELENIUM_AVAILABLE:
        print("Error: Selenium library not found. Please install it.")
        exit(1)
        
    OutreachTool(args).run()

# 📧 MailPilot — Automated Email Outreach CLI

**MailPilot** is a lightweight, local-first Python CLI tool for automating personalized cold email outreach via Gmail. It uses Selenium to compose and send emails through your actual Gmail account — no third-party APIs, no cloud services, no stored credentials.

Built for founders, marketers, and agencies who want to send personalized emails at scale without paying for expensive SaaS tools.

---

## ✨ Features

- **Selenium-powered Gmail automation** — sends through your real Gmail inbox
- **Smart template system** — separate templates for businesses vs. influencers
- **Auto-personalization** — extracts first names from email addresses
- **Personal email detection** — routes Gmail/Yahoo/etc. to influencer templates automatically
- **Follow-up mode** — send follow-ups to previously contacted leads
- **Attachment support** — auto-attach a PDF presentation to every email
- **Gmail signature insertion** — automatically applies your Gmail signature
- **Batch control** — configure how many emails to send per run
- **Anti-spam delays** — randomized delays between sends to avoid spam filters
- **CSV state tracking** — tracks sent/unsent status so you never double-send
- **Persistent browser session** — stay logged in across runs

---

## 📁 Project Structure

```
├── outreach_tool.py          # Main CLI script
├── clients.csv               # Your contact list (email, status)
├── email_template.txt        # Default outreach template
├── influencertemplate.txt    # Template for personal/influencer emails
├── followup_template.txt     # Follow-up template
├── presentation.pdf          # (Optional) PDF attachment
├── requirements.txt          # Python dependencies
└── chrome_data/              # Persistent Chrome profile (gitignored)
```

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare your contacts

Edit `clients.csv` with your list:

```csv
email,status
john@example.com,
jane@startup.io,
```

Leave the `status` column empty for new contacts. The tool marks them as `sent` after successful delivery.

### 3. Customize your templates

Edit `email_template.txt`, `influencertemplate.txt`, and `followup_template.txt` with your messaging. Use `{First Name}` as a placeholder for auto-personalization.

### 4. Run

```bash
python3 outreach_tool.py
```

The tool will:
1. Launch a Chrome browser
2. Prompt you to log into Gmail (first run only — session persists)
3. Send personalized emails to all unsent contacts

---

## ⚙️ Options

| Flag | Description | Default |
|---|---|---|
| `--batch N` | Max emails to send per run | `100` |
| `--followup` | Use the follow-up template instead | `false` |
| `--force-influencer` | Force the influencer template for all emails | `false` |

### Examples

```bash
# Send first 20 emails
python3 outreach_tool.py --batch 20

# Send follow-ups
python3 outreach_tool.py --followup

# Force influencer template for everyone
python3 outreach_tool.py --force-influencer
```

---

## 🔒 Security

- **No credentials stored** — Gmail login happens in a real browser session
- **No external APIs** — everything runs locally on your machine
- **Persistent Chrome profile** — stored in `chrome_data/` (gitignored)
- **The PDF attachment and contact list are gitignored by default**

---

## 📋 How It Works

1. Reads contacts from `clients.csv`
2. Detects personal vs. business emails and selects the right template
3. Personalizes each email with the recipient's first name
4. Opens Gmail compose via URL with pre-filled fields
5. Optionally attaches a PDF and inserts your Gmail signature
6. Sends via `Cmd+Enter` keyboard shortcut
7. Updates the CSV to mark the contact as `sent`
8. Waits a random 15–45 seconds between sends

---

## ⚠️ Disclaimer

This tool is intended for **legitimate business outreach only**. Always comply with applicable anti-spam laws (CAN-SPAM, GDPR, etc.). The author is not responsible for misuse.

---

## 📄 License

MIT

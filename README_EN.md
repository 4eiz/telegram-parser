# 🇬🇧 Telegram Search Parser

**Languages:**
🇷🇺 Русский — [README.md](README.md)  
🇬🇧 English — this file

**Telegram Search Parser** is a tool for bulk searching Telegram channels and chats by keywords, with support for:

* multiple accounts (each with its own `.json` + `.session` pair),
* proxy usage,
* deep query expansion (deep-search),
* filtering results into *channels* and *chats*,
* logging and error handling,
* automatic results saving.

Useful for OSINT, marketing research, audience analytics, and segmentation.

---

## 🔥 Features

| Feature                    | Description                                                                            |
| -------------------------- | -------------------------------------------------------------------------------------- |
| Keyword search             | Searches channels and chats using words/phrases from `queries.txt`.                    |
| Deep Search                | Automatically expands queries (`reddit → reddit a, reddit b, reddit 0..9`).            |
| Result classification      | Correctly distinguishes **channels (broadcast)** and **chats/megagroups (megagroup)**. |
| Multi-account support      | Each account operates with its own `.session` and `.json` files.                       |
| Proxy support              | Proxies are loaded from `proxy.txt` and can differ per account.                        |
| Telegram anti-limit safety | Randomized delays and backoff protection to reduce ban risks.                          |
| Automatic result saving    | Results are saved into `results_channels.txt` and `results_chats.txt`.                 |

---

## 📂 Requirements

* **Python 3.10+**
* Telegram accounts (each pair must look like:
  `111111111.json` + `111111111_telethon.session`)
* If using proxies — working SOCKS5 / HTTP proxies.

---

## 🗂️ Project Structure

```
project/
├─ main.py                  # entry point
├─ queries.txt              # search keywords
├─ proxy.txt                # proxy list (optional)
├─ results_channels.txt     # found channels
├─ results_chats.txt        # found chats
├─ Accounts/                # place *.json + *_telethon.session here
└─ tgparser/
   ├─ accounts.py
   ├─ client.py
   ├─ parser.py
   ├─ deepsearch.py
   ├─ proxies.py
   ├─ config.py
   └─ ...
```

---

## ⚙️ Installation

```bash
git clone https://github.com/USERNAME/REPO.git
cd REPO

python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

---

## 🔧 Configuration

1. Rename `.env.example` → `.env`
2. Configure deep search behavior:

```env
DEEP_SEARCH=1         # enable/disable deep search
LIMIT=200             # total results limit
```

3. Put account files into `Accounts/`:

```
123456789.json
123456789_telethon.session
```

4. Add keywords to `queries.txt`:

```
Reddit
Crypto
News
```

---

## 🚀 Running

```bash
python main.py
```

---

## 📄 Output

After execution, the following files will appear:

```
results_channels.txt
results_chats.txt
```

Line format:

```
Name | Members count | Link
```
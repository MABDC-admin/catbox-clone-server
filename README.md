# Catbox Clone Server

A beautifully styled, self-hosted file sharing server built with Python and Flask. This server acts as a direct clone of services like `catbox.moe` but gives you complete control over your files.

### Features
- **Unlimited File Sizes**: Upload files of absolutely any size (the only limit is your hard drive space).
- **Direct Links**: Downloaded files open natively in your browser (e.g., MP3s and MP4s will stream/play instantly rather than forcing a download).
- **Beautiful Interface**: A modern UI utilizing glassmorphism, responsive design, and smooth drag-and-drop mechanics.
- **Lightweight**: Written entirely in one Python file. No messy dependencies or complicated databases.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/MABDC-admin/catbox-clone-server.git
cd catbox-clone-server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
python file_server.py
```

The server will be available at `http://localhost:5000`. Any uploaded files will be stored in the newly generated `uploads/` directory.

## Exposing it to the internet
If you want to host it so you can upload from your phone or share links with friends, simply use a free tunneling service like Localtunnel or Pinggy:

**Using Localtunnel (Requires Node.js):**
```bash
npx localtunnel --port 5000
```

**Using Pinggy (Requires SSH):**
```bash
ssh -p 443 -R0:localhost:5000 a.pinggy.io
```

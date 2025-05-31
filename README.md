# Python Comic Server ✅ COMPLETED

A local HTTP server for serving CBZ and CBR comic book files from your computer to mobile devices over WiFi.

**Status**: Production Ready | **Version**: 1.0.0 | **Tested**: ✅ Live Mobile Device Testing Complete

## Features

- 📚 Serves CBZ and CBR comic files
- 📱 Mobile app compatible (iOS comic readers) - **TESTED & WORKING**
- 📊 Real-time bandwidth monitoring - **IMPLEMENTED & TESTED**
- 🔄 Support for large files (up to 3GB) - **MEMORY EFFICIENT STREAMING**
- ⚡ Concurrent downloads - **THREADING SUPPORT**
- 🔒 Security protections - **PATH TRAVERSAL PROTECTION**
- 🌐 Range request support for resumable downloads - **HTTP/1.1 COMPLIANT**

## Quick Start

1. **Install Python 3.7+** (no additional packages required)

2. **Run the server:**
   ```bash
   python server.py
   ```

3. **Add comic files** to the `comics` directory

4. **Connect from your mobile device:**
   - Use the URL displayed when the server starts
   - Example: `http://192.168.1.100:8000`

## Usage

### Basic Usage
```bash
python server.py
```

### Custom Port
```bash
python server.py --port 8080
```

### Custom Directory
```bash
python server.py --dir "C:\My Comics"
```

### Combined Options
```bash
python server.py --port 9000 --dir "./my-comics"
```

## Requirements

- Python 3.7 or higher
- No external dependencies (uses only Python standard library)
- Network access (WiFi recommended)

## Supported File Types

- `.cbz` (Comic Book ZIP)
- `.cbr` (Comic Book RAR)

## Security Features

- Path traversal protection
- Local network access only
- Request validation
- No system file exposure

## Mobile App Setup

1. Connect your device to the same WiFi network as your computer
2. Open your comic reader app
3. Add a new server with the URL shown by the Python Comic Server
4. Browse and download comics directly to your device

## Project Structure

```
Comics-Web-Server/
├── server.py              # Main server application
├── config.py              # Configuration management
├── comic_handler.py       # HTTP request handler
├── bandwidth_monitor.py   # Bandwidth monitoring
├── comics/                # Default comic files directory
└── README.md              # This file
```

## License

See LICENSE file for details.
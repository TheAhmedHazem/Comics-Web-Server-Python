# Python Comic Server - Quick Start Guide

## Prerequisites
- Python 3.7 or higher
- CBZ/CBR comic files
- Local WiFi network

## Installation

1. **Download the server files**:
   - `server.py` (main server)
   - `config.py` (configuration)
   - `bandwidth_monitor.py` (monitoring)
   - `comic_handler.py` (request handler)

2. **Create a comics directory**:
   ```bash
   mkdir comics
   ```

3. **Add your comic files**:
   - Copy `.cbz` and `.cbr` files to the `comics` directory
   - Only CBZ and CBR files will be served (security feature)

## Usage

### Simple Start (Default Settings)
```bash
python server.py
```
- **Port**: 8000
- **Directory**: `./comics`
- **Host**: All interfaces (0.0.0.0)

### Custom Configuration
```bash
python server.py --port 8080 --directory /path/to/comics --host 192.168.1.100
```

### Command Line Options
- `--port` or `-p`: Server port (default: 8000)
- `--directory` or `-d`: Comics directory path (default: ./comics)
- `--host`: Server host/IP (default: 0.0.0.0)

## Finding Your Server IP

### Windows
```powershell
ipconfig
```
Look for "IPv4 Address" under your WiFi adapter.

### macOS/Linux
```bash
ifconfig
```
Look for your WiFi interface IP address.

## Accessing Your Comics

### From a Web Browser
1. Open browser on your mobile device
2. Navigate to: `http://YOUR-SERVER-IP:8000`
3. Browse and download comic files

### From Comic Reader Apps
Most mobile comic reader apps support network sources:
1. Add a new source/server
2. Enter: `http://YOUR-SERVER-IP:8000`
3. Browse your comic collection

## Features

### Real-Time Monitoring
The server displays real-time information:
- Active connections
- Transfer speeds
- Bandwidth usage
- File access logs

### Large File Support
- Supports files up to 3GB
- Memory-efficient streaming
- Resume/seek support for mobile apps

### Security
- Only serves CBZ/CBR files
- Path traversal protection
- Request validation

## Troubleshooting

### "Connection Reset" Errors
These are normal when mobile devices close connections. The downloads still complete successfully.

### Firewall Issues
Make sure your firewall allows Python on the chosen port.

### Network Access
Ensure your mobile device and server are on the same WiFi network.

### Performance
For optimal performance:
- Use wired connection for server if possible
- Ensure strong WiFi signal on mobile device
- Close other bandwidth-intensive applications

## Mobile App Recommendations

The server works with most comic reader apps that support network sources:
- **iOS**: ComicFlow, YACReader, Panels
- **Android**: CDisplayEx, ComicScreen, Perfect Viewer

## Support

For issues or questions, check the console output for detailed error messages and transfer statistics.

---
**Python Comic Server v1.0.0** - Serving comics to mobile devices made simple!

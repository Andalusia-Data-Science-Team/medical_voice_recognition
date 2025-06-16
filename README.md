# Medical Voice Assistant 🩺

A voice-enabled medical assistant application powered by Fireworks AI, designed to provide intelligent medical information and support through natural voice interactions.

## Features

- **Voice Recognition**: Real-time speech-to-text processing
- **AI-Powered Responses**: Medical knowledge powered by Fireworks AI
- **Cross-Platform Support**: Compatible with Windows, macOS, and Linux
- **GUI Interface**: User-friendly desktop application
- **Medical Focus**: Specialized for healthcare and medical queries

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **Node.js** - [Download Node.js](https://nodejs.org/)
- **PortAudio** - Required for audio processing
- **Fireworks AI API Key** - [Get your API key](https://fireworks.ai/)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/medical-voice-assistant.git
cd medical-voice-assistant
```

### 2. Environment Configuration

Create a `.env` file in the project root directory and add your Fireworks AI API key:

```env
FIREWORKS_API_KEY=your_api_key_here
```

### 3. Python Environment Setup

Create and activate a virtual environment:

**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 4. Install PyAudio

PyAudio installation varies by operating system:

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

**Windows:**
```bash
# Download the appropriate PyAudio wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
# Example for Python 3.11, 64-bit:
pip install PyAudio-0.2.11-cp311-cp311-win_amd64.whl
```

### 5. Install Project Dependencies

```bash
pip install -e .
```

### 6. Client Dependencies (GUI)

Navigate to the client directory and install Node.js dependencies:

**Windows (if Node.js not installed):**

First, download and install the latest Node.js version:

1. **Download Node.js**
   In PowerShell, run:
   ```powershell
   Start-Process "https://nodejs.org/en/download" -Wait
   ```
   This opens the official Node.js site.
   - Click on the **"LTS"** version (e.g., "18.x.x LTS") for Windows.
   - Download the `.msi` installer.

2. **Run the Installer**
   - Double-click the downloaded `.msi` file.
   - Follow the installer:
     - ✅ Select "Add to PATH" (default)
     - ✅ Accept all defaults unless you know otherwise

3. **Install Dependencies**
   ```bash
   npm install
   ```

**macOS/Linux:**
```bash
npm install
```

## Usage

### Starting the Server

1. Ensure your virtual environment is activated
2. Start the backend server:

```bash
python -m src.controller.app
```

### Starting the Client (GUI)

1. Open a new terminal window

2. Start the GUI application:

```bash
npm start
```

## Project Structure

```
medical-voice-assistant/
├── src/
│   ├── controller/
│   │   └── app.py
│   └── model/
│   │   └── audio_preprocessing.py
│   │   └── file_service.py
│   │   └── speech_service.py
│   │   └── input_validator.py
│   │   └── llm_service.py
│   │   └── pipeline.py
│   └── view/
│   │   └── index.html
│   │   └── main.js
│   └── core/
│   │   └── database.py
│   │   └── config.py
├── .env
├── setup.cfg
├── pyproject.toml
├── setup.py
├── data_latest.parquet
├── .gitignore
└── README.md
```

## Troubleshooting

### Common Issues

**PyAudio Installation Errors:**
- Ensure PortAudio is properly installed on your system
- On Windows, use pre-compiled wheel files
- On macOS, install via Homebrew first

**API Key Issues:**
- Verify your Fireworks AI API key is correct
- Check that the `.env` file is in the project root
- Ensure the API key has proper permissions

**Audio Device Issues:**
- Verify your microphone is working and accessible
- Check system audio permissions
- Test with other audio applications

**Node.js Installation Issues (Windows):**
- Restart your terminal/PowerShell after installation
- Verify installation by running `node --version` and `npm --version`
- If PATH issues occur, manually add Node.js to your system PATH

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `FIREWORKS_API_KEY` | Your Fireworks AI API key | Yes |

### Audio Settings

The application uses your system's default microphone. Ensure:
- Microphone permissions are granted
- Audio drivers are up to date
- No other applications are blocking microphone access

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the [Fireworks AI documentation](https://docs.fireworks.ai/)
- Review the troubleshooting section above

## Acknowledgments

- [Fireworks AI](https://fireworks.ai/) for providing the AI capabilities
- [PyAudio](https://pypi.org/project/PyAudio/) for audio processing
- Contributors and maintainers

---

**Note**: This application is designed for educational and informational purposes. Always consult with qualified healthcare professionals for medical advice.
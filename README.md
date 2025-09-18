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
- **FFmpeg** - Required for audio handling ([Download FFmpeg](https://ffmpeg.org/download.html))  
- **Fireworks AI API Key** - [Get your API key](https://fireworks.ai/)  

---

## FFmpeg Installation  

### Windows
1. Download the **static build** from [FFmpeg Windows builds](https://www.gyan.dev/ffmpeg/builds/).  
2. Extract the ZIP file (e.g., to `C:\ffmpeg`).  
3. Add FFmpeg to PATH:  
   - Press **Win + R** → type `sysdm.cpl` → **Advanced** → **Environment Variables**  
   - Edit the `Path` variable → Add:  
     ```
     C:\ffmpeg\bin
     ```
4. Verify installation:  
   ```powershell
   ffmpeg -version
   ```

### macOS
```bash
brew install ffmpeg
ffmpeg -version
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg -y
ffmpeg -version
```

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/medical-voice-assistant.git
cd medical_voice_recognition
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
**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

**Windows:**
```bash
# Download precompiled wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
pip install PyAudio-0.2.11-cp311-cp311-win_amd64.whl
```

### 5. Install Project Dependencies
```bash
pip install -e .
```

### 6. Client Dependencies (GUI)
Navigate to the client directory and install Node.js dependencies:

**macOS/Linux/Windows:**
```bash
npm install
```

---

## Usage

### Starting the Server
1. Ensure your virtual environment is activated  
2. Start the backend server with Uvicorn:  
```bash
uvicorn src.controller.app:app --reload
```

### Starting the Client (GUI)
1. Open a new terminal window  
2. Start the GUI application:  
```bash
npm start
```

---

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

---

## Troubleshooting

**PyAudio Errors:** Install PortAudio first, use wheel on Windows.  
**FFmpeg Not Found:** Ensure it’s installed and added to PATH.  
**API Key Issues:** Confirm `.env` file and key permissions.  
**Audio Issues:** Check microphone permissions and drivers.  
**Node.js Issues (Windows):** Restart terminal after install, verify with `node -v` and `npm -v`.  

---

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `FIREWORKS_API_KEY` | Your Fireworks AI API key | Yes |

---

## Contributing
1. Fork repo  
2. Create branch (`git checkout -b feature/amazing-feature`)  
3. Commit changes  
4. Push branch (`git push origin feature/amazing-feature`)  
5. Open PR  

---

## License
MIT License – see [LICENSE](LICENSE).  

---

## Support
- GitHub Issues  
- [Fireworks AI docs](https://docs.fireworks.ai/)  

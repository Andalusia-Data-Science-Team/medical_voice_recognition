# 🩺 Medical Voice Assistant

A voice-enabled assistant tailored for medical applications, powered by advanced AI models from Fireworks AI.

---

## 🚀 Getting Started

Follow these steps to set up and run the Medical Voice Assistant on your machine.

---

### 1. 🔐 Set Up API Key

Create a `.env` file in the root directory and add your Fireworks AI API key:


---

### 2. 🐍 Create and Activate Virtual Environment

Create a Python virtual environment and activate it:

```bash
# Create venv
python -m venv venv

# Activate (choose your OS)
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

3. 🎙️ Install PyAudio (OS-specific instructions)
Ensure PortAudio/PyAudio is installed, as it is required for audio processing.

macOS:
brew install portaudio

Linux (Ubuntu/Debian):
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio

Windows:
Download and install the appropriate .whl file for PyAudio:
pip install PyAudio‑0.2.11‑cp311‑cp311‑win_amd64.whl


4. 📦 Install Project Dependencies (Editable Mode)
Run the following command from the root directory:
pip install -e .


5. 🖥️ Run the Server
In a new terminal (with the virtual environment activated), start the server:
python -m src.controller.app

6. 💻 Run the Client (GUI Machine Only)
Requires a GUI-enabled machine (Desktop Linux, macOS, or Windows)

In a separate terminal, navigate to the client folder (if applicable), and run:
npm install
npm start

🩺 Medical Voice Assistant Setup Guide
A voice-enabled assistant for medical applications, powered by Fireworks AI.
🚀 Setup Instructions
Follow these steps to set up and run the Medical Voice Assistant on your machine.
Prerequisites

Python 3.8 or higher
Node.js (for GUI client)
PortAudio (for audio processing)
Fireworks AI API key

Step 1: 🔐 Configure API Key

Create a .env file in the project root directory.
Add your Fireworks AI API key:

FIREWORKS_API_KEY=your_api_key_here

Step 2: 🐍 Set Up Python Virtual Environment

Create a virtual environment:

python -m venv venv


Activate the virtual environment:
macOS/Linux:source venv/bin/activate


Windows:venv\Scripts\activate





Step 3: 🎙️ Install PyAudio
PyAudio is required for audio processing. Install it based on your operating system:

macOS:
brew install portaudio
pip install pyaudio


Linux (Ubuntu/Debian):
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio


Windows:

Download the appropriate PyAudio wheel file (e.g., PyAudio-0.2.11-cp311-cp311-win_amd64.whl) from a trusted source.
Install it:pip install PyAudio-0.2.11-cp311-cp311-win_amd64.whl





Step 4: 📦 Install Project Dependencies
With the virtual environment activated, install the project in editable mode:
pip install -e .

Step 5: 🖥️ Run the Server
In a terminal with the virtual environment activated, start the server:
python -m src.controller.app

Step 6: 💻 Run the Client (GUI-Enabled Machines Only)
The client requires a GUI-enabled machine (Desktop Linux, macOS, or Windows).

Navigate to the client directory (if applicable):

cd client


Install Node.js dependencies:

npm install


Start the client:

npm start

Notes

Ensure your system has a working microphone for voice input.
The server and client must be run in separate terminals.
For issues with PyAudio installation, verify PortAudio is correctly installed.
Refer to Fireworks AI documentation for API key usage and limits.


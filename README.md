Installation Guide: Meeting Assistant
This guide will walk you through setting up the Meeting Assistant on your computer.

Part 1: Prerequisites (Things you need first)
Before installing the app, you need a few things:

Python: This is the programming language the app's backend is built on.

Go to the official Python website: https://www.python.org/downloads/
Download and install the latest version for your operating system (Windows or macOS).
On Windows: During installation, make sure to check the box that says "Add Python to PATH".
Google Cloud Account (for Transcription):

You will need a Google Cloud account to use the speech-to-text feature.
Follow this guide to create a service account and download a JSON key file: Google Cloud Authentication Guide. You only need to follow the steps to create and download the JSON key file. Keep this file safe!
OpenAI API Key (for AI Analysis):

You need an API key from OpenAI to use the AI analysis features.
Sign up or log in at https://platform.openai.com/.
Go to the "API Keys" section in your account and create a new secret key. Copy this key and save it somewhere secure.
Part 2: Setting Up the Backend
This part configures the "brain" of the application.

Download the Code:

Download the project files as a ZIP and extract them to a folder on your computer (e.g., C:\MeetingAssistant or ~/Documents/MeetingAssistant).
Open a Terminal (Command Prompt):

Windows: Press the Windows key, type cmd, and press Enter.
macOS: Open the "Terminal" app from your Applications/Utilities folder.
Navigate to the backend directory using the cd command. For example:
cd C:\MeetingAssistant\backend
Create a Virtual Environment:

This creates an isolated space for the app's dependencies. In your terminal, run:
python -m venv venv
Activate the Environment:

Windows:
venv\Scripts\activate
macOS:
source venv/bin/activate
You will see (venv) at the beginning of your terminal prompt, which means it's active.
Install Required Packages:

With the environment active, run this command to install all the necessary libraries:
pip install -r requirements.txt
Set Your API Keys (Environment Variables):

This is a crucial step to give the app access to the Google and OpenAI services.

For Google Cloud: You need to tell the app where your downloaded JSON key file is.

For OpenAI: You need to provide the secret key you copied.

On Windows (in the same terminal):

setx GOOGLE_APPLICATION_CREDENTIALS "C:\path\to\your\google-key.json"
setx OPENAI_API_KEY "your-openai-api-key-goes-here"
Replace the path and key with your actual ones. After running these commands, you must close and reopen the terminal for the changes to take effect.

On macOS (in the same terminal):

export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/google-key.json"
export OPENAI_API_KEY="your-openai-api-key-goes-here"
Note: This command sets the keys for the current terminal session only. For a permanent solution, you would add these lines to your ~/.zshrc or ~/.bash_profile file.

Run the Backend Server:

Make sure you are in the backend directory and your virtual environment is active. Then, run:
python main.py
You should see messages indicating that the WebSocket and HTTP servers have started. Keep this terminal window open!
Part 3: Using the Frontend
Open the Application:

Navigate to the frontend folder in your file explorer.
Double-click the index.html file. It should open in your default web browser.
Start a Recording:

Select your language from the dropdown menu.
Click the "Start/Stop Recording" button to begin. Your browser will ask for permission to use your microphone. Click "Allow."
As you speak, you will see the live transcript and AI analysis appear on the screen.
Part 4: Integrating with Zoom, Teams, etc.
To analyze audio from a meeting, you need to route the meeting's audio into the app.

Install a Virtual Audio Cable:

Windows: Download and install VB-CABLE.
macOS: Download and install BlackHole.
Configure Audio Settings:

In your video conferencing app (Zoom, Teams, etc.), go to Audio Settings.
Change the Speaker or Audio Output to the virtual audio device you just installed (e.g., "CABLE Input" or "BlackHole").
Now, the audio from your meeting will be sent to the virtual cable instead of your speakers.
Start the Assistant:

In the Meeting Assistant web app, click "Start/Stop Recording." It will now listen to the audio from the virtual cable, transcribing and analyzing your meeting in real-time.
You are all set! If you run into any issues, double-check that the backend server is still running and that the API keys were set correctly.

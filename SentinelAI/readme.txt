README.TXT
SentinelAI – How to Run the Project

--------------------------------------------------
1. PREREQUISITES
--------------------------------------------------
- Python 3.9 or higher
- Ollama installed
- Internet access (for initial model download)

--------------------------------------------------
2. INSTALL DEPENDENCIES
--------------------------------------------------
Open a terminal in the project folder and run:

python -m pip install fastapi uvicorn requests

--------------------------------------------------
3. START THE LLM (OLLAMA)
--------------------------------------------------
Run the following command:

ollama run llama3

Leave this running in the background.

--------------------------------------------------
4. START THE SERVER
--------------------------------------------------
In a new terminal window, from the project directory:

python -m uvicorn server:app --reload

You should see:
Uvicorn running on http://127.0.0.1:8000

--------------------------------------------------
5. OPEN THE WEB INTERFACE
--------------------------------------------------
Open a browser and navigate to:

http://127.0.0.1:8000

--------------------------------------------------
6. USING THE DEMO
--------------------------------------------------
1. Select a preset snapshot or paste your own
2. Click 'Run Agent'
3. Review the generated intelligence output
4. Copy or discuss results during interview

--------------------------------------------------
7. STOPPING THE APPLICATION
--------------------------------------------------
- Stop server: Ctrl + C
- Stop Ollama: Ctrl + C in Ollama terminal

--------------------------------------------------
8. TROUBLESHOOTING
--------------------------------------------------
- If the page shows {"ok": true}, the server is running
- Ensure Ollama is running if no output appears
- Reinstall dependencies if imports fail

--------------------------------------------------
9. INTERVIEW NOTE
--------------------------------------------------
Focus discussion on architecture, autonomy, and reasoning rather than UI details.

--------------------------------------------------
10. DISCLAIMER
--------------------------------------------------
This project is a demonstration of AI-agent architecture and does not provide financial or investment advice.

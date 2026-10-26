Install this project in your system, Enter the API Key generated from your LLM, and Use. 
Future Scope, Animated boardroom, just the frontend needs to be updated and backend model stays the same

To Update API key
**Step 1: Configure your API key**
Copy and paste this command into your existing PowerShell window:
$env:OPENAI_API_KEY="YOUR_ACTUAL_API_KEY"


Replace YOUR_ACTUAL_API_KEY with your real OpenAI API key.

Press Enter. You won't see any confirmation, which is normal.
**Step 2: Verify the API key**
Run:
.\.venv\Scripts\python.exe -c "import os; print('API Key: Configured' if os.getenv('OPENAI_API_KEY') else 'API Key: Missing')"


Expected result:
API Key: Configured

This confirms that Python can see the key, not yet that OpenAI has accepted it.
**Step 3: Start Boardroom OS**
Run:
.\.venv\Scripts\python.exe -m uvicorn app:app --reload


**Step 4: Open your boardroom**
Visit:

**http://127.0.0.1:8000**

Refresh the page using Ctrl + Shift + R.

If the application detects the key successfully, it should no longer display DEMO MODE · API KEY NEEDED.

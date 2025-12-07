# AI Agent Conversation & Debate System

Two AI agents that communicate through spoken conversation. Supports both casual conversation mode and structured debate mode with a web interface.

## What you need

- Windows
- Python 3.8 or newer
- Ollama with gemma2:2b model (or gemma3:1b)

## Setup

Install Ollama from [ollama.ai](https://ollama.ai/download/windows) and get the model:

```bash
ollama pull gemma2:2b
```

Install Python packages:

```bash
pip install -r requirements.txt
```

## Mode 1: Casual Conversation (Terminal)

Run the conversation mode:

```bash
python agent_conversation.py
```

You'll get a menu to pick topics, conversation length, and voices.

## Mode 2: Debate Arena (Web Interface)

Run the web server:

```bash
python debate_web_app.py
```

Then open your browser to:
```
http://localhost:5000
```

### Debate Features

- **Structured Format**: Opening → Arguments → Rebuttals → Closing
- **Clear Sides**: One agent argues FOR, one argues AGAINST
- **Visual Interface**: See who's speaking with highlighted cards
- **Synced Text**: Text types in real-time as the voice speaks
- **Full Transcript**: Complete debate log at the bottom

### Using the Web Interface

1. Enter your debate topic (e.g., "AI will replace human jobs")
2. Click "Start Debate"
3. Click "Next Turn" to progress through the debate
4. Watch as agents take turns with synced text and audio
5. Scroll down to see the full transcript

## File Structure

```
ai-agents/
├── agent_conversation.py    # Casual conversation mode
├── debate_web_app.py        # Web debate mode (Flask server)
├── requirements.txt         # Dependencies
├── README.md               # This file
├── templates/              # Created automatically
│   └── debate.html        # Web interface
└── static/                # Created automatically
    └── audio_*.mp3        # Temporary audio files
```

## Setup Files

After first run, save the HTML template:

Create `templates/debate.html` and paste the HTML content from the artifacts.

## Customizing

### Change Debate Agents

Edit `debate_web_app.py`:

```python
agent_for = DebateAgent(
    name="Alex",
    stance="FOR",
    role="Your custom role description",
    voice="en-US-GuyNeural"
)
```

### Adjust Debate Structure

Modify the phases in `DebateManager.__init__`:

```python
self.debate_structure = [
    ("opening", "Opening Statement", 2),  # 2 turns
    ("argument", "Main Arguments", 4),    # 4 turns
    ("rebuttal", "Rebuttals", 2),        # 2 turns
    ("closing", "Closing Statement", 2)   # 2 turns
]
```

### Change Model

Both scripts use the model specified in the code. To change:

```python
model='gemma2:2b'  # or 'gemma3:1b', 'llama3.2:3b', etc.
```

## Troubleshooting

**Flask not found**
```bash
pip install flask flask-cors
```

**Port already in use**
Change the port in `debate_web_app.py`:
```python
app.run(debug=True, port=5001)  # Use different port
```

**Audio not playing in browser**
- Check browser console for errors
- Make sure the `static` folder exists
- Try a different browser (Chrome/Edge recommended)

**Text not syncing with audio**
- This can happen if audio loads slowly
- The typing speed is calculated based on audio duration
- Refresh the page and try again

**Ollama connection issues**
Make sure Ollama is running:
```bash
ollama serve
```

## Available Voices

- Guy, Christopher, Eric (American male)
- Jenny, Aria, Sara (American female)
- Ryan, Sonia (British)

Run `edge-tts --list-voices` to see all options.

That's it! Choose conversation mode for casual chat or debate mode for structured arguments.
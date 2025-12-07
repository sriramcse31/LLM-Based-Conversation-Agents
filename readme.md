# AI Agent Conversation System

Two AI agents that communicate through spoken conversation with text syncing in real-time.

## What you need

- Windows
- Python 3.8 or newer
- Ollama with gemma2:2b model

## Setup

Install Ollama from [ollama.ai](https://ollama.ai/download/windows) and get the model:

```bash
ollama pull gemma2:2b
```

Install Python packages:

```bash
pip install -r requirements.txt
```

## Running the System

```bash
python agent_conversation.py
```

You'll get an interactive menu to:
- Choose a conversation topic (or enter your own)
- Set the number of conversation turns
- Select voice pairs for the agents

### Conversation Structure
- Agents stay on topic with periodic guidance prompts
- Conversations progress through different angles (challenges, future evolution, practical actions)
- Sanitized conversation history prevents pattern reinforcement

**Note:** Small models (2-3B parameters) struggle to consistently follow these rules despite heavy prompting.

## Agent Roles

**Agent 1 - Technical Analyst**
- Provides concise, technical responses
- Focuses on specific tools, frameworks, and implementation details
- Analytical and precise

**Agent 2 - Strategic Critic**
- Challenges assumptions and identifies limitations
- Asks probing questions about business impact and risks
- Direct and questioning

## Customization

### Change the Model

Edit `agent_conversation.py`:
```python
response = ollama.generate(
    model='gemma3:1b',  # or 'llama3.2:3b', 'mistral:7b', etc.
```

### Adjust Response Length

Change `num_predict` in the `think()` method:
```python
'num_predict': 100,  # Lower = shorter, Higher = longer
```

### Modify Agent Personalities

Edit the agent creation in `main()`:
```python
agent1 = Agent(
    name="Alex",
    personality="Your custom personality here...",
    voice="en-US-GuyNeural"
)
```

### Change Speech Rate

In the `speak()` method:
```python
communicate = edge_tts.Communicate(text, self.voice, rate="+15%")
# Increase: "+25%", "+30%" (faster)
# Decrease: "+5%", "+0%" (slower)
```

## Troubleshooting

### Ollama Issues

**Problem:** Connection refused or model not found
```bash
# Start Ollama
ollama serve

# Verify model is installed
ollama list
ollama pull gemma2:2b
```

### Module Not Found

```bash
pip install -r requirements.txt
```

## Known Limitations

### Model Instruction Following
Small models (1-3B parameters) have difficulty consistently following complex rules:
- Filler words still appear despite explicit bans
- Agents may mirror each other's speaking patterns
- Conversations can become repetitive or circular

**This is a fundamental limitation of small language models, not a bug.**

For better results, use larger models (7B+) if your hardware supports it.

### Text Syncing Accuracy
Text typing speed is calculated based on audio duration. Slight desyncs may occur if:
- Audio loads slowly
- System is under heavy load
- TTS generation varies in speed

## Project Structure

```
ai-agents/
├── agent_conversation.py    # Main application
├── requirements.txt         # Dependencies
├── README.md               # This file
└── temp_*.mp3              # Temporary audio files (auto-deleted)
```

## How It Works

1. **Agent thinks:** Generates response using local LLM (Ollama)
2. **Text-to-Speech:** Converts response to audio using Edge TTS
3. **Synced Display:** Calculates typing speed based on audio duration
4. **Simultaneous Play:** Plays audio while typing text character-by-character
5. **History Sanitization:** Cleans filler words before storing in conversation history
6. **Turn Management:** Alternates speakers with topic guidance at key turns

## Example Topics

Technical:
- "Impact of AI on software QA engineers"
- "Microservices vs monolithic architecture trade-offs"
- "Security challenges in IoT devices"

General:
- "Should humanity colonize Mars?"
- "Impact of social media on society"
- "Future of remote work"

The system works best with topics that have clear pro/con arguments or multiple perspectives.

---

**Note:** This is an experimental system showcasing AI agent interaction. Conversation quality depends heavily on the underlying language model's capabilities.
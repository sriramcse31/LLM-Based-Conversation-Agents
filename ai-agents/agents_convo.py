import ollama
import edge_tts
import pygame
import os
import time
import re
from typing import List, Dict

class Agent:
    """An AI agent that can speak and listen"""
    
    # Class-level event loop for Windows compatibility
    _event_loop = None
    
    def __init__(self, name: str, personality: str, voice: str = "en-US-GuyNeural"):
        self.name = name
        self.personality = personality
        self.role = ""  # Will be set based on personality
        self.conversation_history: List[Dict[str, str]] = []
        self.voice = voice
        self.topics_covered = set()  # Track what's been discussed
        
        # Initialize pygame mixer for audio playback
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        # Initialize event loop once for all agents
        if Agent._event_loop is None:
            import asyncio
            Agent._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(Agent._event_loop)
        
    def speak(self, text: str):
        """Convert text to speech and play it with synced text display"""
        # Validate text before speaking
        if not text or len(text.strip()) < 5:
            print(f"\n{self.name}: [no response]")
            return
            
        print(f"\n{self.name}: ", end='', flush=True)
        
        try:
            # Generate speech file
            audio_file = f"temp_{self.name}.mp3"
            communicate = edge_tts.Communicate(text, self.voice, rate="+15%")
            
            # Use the class-level event loop to avoid Windows errors
            Agent._event_loop.run_until_complete(communicate.save(audio_file))
            
            # Get audio duration for sync calculation
            from mutagen.mp3 import MP3
            try:
                audio_info = MP3(audio_file)
                audio_duration = audio_info.info.length
            except:
                # Fallback: estimate duration (roughly 150 words per minute)
                words = len(text.split())
                audio_duration = (words / 150) * 60
            
            # Calculate typing delay to match audio duration
            char_delay = audio_duration / len(text) if len(text) > 0 else 0
            
            # Load and start playing audio
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            
            # Type text character by character in sync with audio
            for char in text:
                print(char, end='', flush=True)
                time.sleep(char_delay)
            
            print()  # New line after text completes
            
            # Wait for audio to finish (if any remaining)
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # Clean up
            pygame.mixer.music.unload()
            time.sleep(0.2)
            
            try:
                os.remove(audio_file)
            except:
                pass
                
        except Exception as e:
            # Fallback: just print the text if audio fails
            print(text)
            print(f"⚠️ Speech error: {e}")
    
    def think(self, prompt: str) -> str:
        """Generate a response using the local Gemma model"""
        # Build context from conversation history
        context = f"You are {self.name}. {self.personality}\n\n"
        
        # Add recent conversation history
        if self.conversation_history:
            context += "Conversation so far:\n"
            for msg in self.conversation_history[-6:]:
                context += f"{msg['speaker']}: {msg['content']}\n"
        
        context += f"\nNow respond to: {prompt}\n"
        context += f"IMPORTANT: Respond conversationally as if talking to a friend. Keep your response to 2-3 sentences maximum. Use natural spoken language - contractions, casual phrases, and a relaxed tone. Share your thoughts briefly. No asterisks, actions, or tone descriptions.\n{self.name}:"
        
        # Call Ollama
        response = ollama.generate(
            model='gemma3:1b',
            prompt=context,
            options={
                'temperature': 0.8,
                'top_p': 0.9,
                'num_predict': 80,  # Shorter for concise responses
                'num_ctx': 2048,
                'num_thread': 4
            }
        )
        
        # Clean up the response
        response_text = response['response'].strip()
        
        # Remove formatting artifacts
        response_text = re.sub(r'\*[^*]*\*', '', response_text)  # Remove *actions*
        response_text = re.sub(r'\([^)]*\)', '', response_text)  # Remove (tone)
        response_text = re.sub(r'\[[^\]]*\]', '', response_text)  # Remove [actions]
        response_text = ' '.join(response_text.split())  # Clean whitespace
        
        return response_text
    
    def sanitize_response(self, text: str) -> str:
        """Clean up response by removing filler words and fixing patterns"""
        if not text:
            return ""
            
        sanitized = text
        
        # Remove filler words and phrases
        filler_patterns = [
            (r'\b(okay|ok),?\s+so\b', ''),
            (r'\bhonestly,?\s*', ''),
            (r'\bseriously,?\s*', ''),
            (r'\bkinda\b', 'somewhat'),
            (r'\bliterally\b', ''),
            (r'\bpretty\b(?!\s+\w+\s+(good|bad|important))', ''),
            (r'\breally\b', ''),
            (r'\bactually\b', ''),
            (r'\byou know\??\s*', ''),
            (r',?\s*right\?', '.'),
            (r',?\s*isn\'t it\?', '.'),
            (r',?\s*don\'t you think\?', '.'),
            (r'\bI think\b', ''),
            (r'\bprobably\b', ''),
        ]
        
        for pattern, replacement in filler_patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        # Clean up extra whitespace and punctuation
        sanitized = re.sub(r'\s+', ' ', sanitized)
        sanitized = re.sub(r'\s+([.,!?])', r'\1', sanitized)
        sanitized = re.sub(r'([.,!?])\1+', r'\1', sanitized)
        sanitized = re.sub(r'^\s*[,.]', '', sanitized)
        
        # Ensure proper capitalization
        sanitized = sanitized.strip()
        if sanitized and len(sanitized) > 0 and sanitized[0].islower():
            sanitized = sanitized[0].upper() + sanitized[1:]
        
        return sanitized
    
    def add_to_history(self, speaker: str, content: str):
        """Add a SANITIZED message to conversation history"""
        # Clean the content before storing
        clean_content = self.sanitize_response(content)
        
        self.conversation_history.append({
            'speaker': speaker,
            'content': clean_content
        })


class ConversationManager:
    """Manages the conversation between two agents"""
    
    def __init__(self, agent1: Agent, agent2: Agent):
        self.agent1 = agent1
        self.agent2 = agent2
        self.turn_count = 0
        self.max_turns = 10
        self.failed_turns = 0
        self.original_topic = ""  # Store the original topic
        
    def get_conversation_prompt(self, turn: int, topic: str) -> str:
        """Generate a prompt that guides the conversation to cover different aspects"""
        if turn == 0:
            self.original_topic = topic  # Save original topic
            return topic
        elif turn <= 3:
            return None  # Let natural flow happen
        elif turn == 4:
            return f"Regarding '{self.original_topic}': What are the practical challenges or limitations?"
        elif turn == 6:
            return f"Back to '{self.original_topic}': How might this evolve in the next few years?"
        elif turn == 8:
            return f"Focusing on '{self.original_topic}': What should people actually do or consider?"
        return None
        
    def start_conversation(self, initial_topic: str):
        """Start a conversation between the two agents"""
        print("\n" + "="*60)
        print(f"CONVERSATION START: {initial_topic}")
        print("="*60)
        
        current_speaker = self.agent1
        current_listener = self.agent2
        current_message = initial_topic
        
        while self.turn_count < self.max_turns:
            # Inject topic guidance at certain points
            guidance_prompt = self.get_conversation_prompt(self.turn_count, initial_topic)
            if guidance_prompt and self.turn_count > 0:
                print(f"💡 New angle: {guidance_prompt}")
                current_message = guidance_prompt
            
            # Agent thinks (time it externally)
            start_time = time.time()
            response = current_speaker.think(current_message)
            thinking_time = time.time() - start_time
            
            # Display thinking time
            print()
            print(f"⏱️  {current_speaker.name} thought for {thinking_time:.2f} seconds")
            
            # Skip if response is empty or too short
            if not response or len(response.strip()) < 15:
                print(f"⚠️ {current_speaker.name} had nothing to say, trying to restart...")
                self.failed_turns += 1
                
                # If too many failed turns, inject a new topic
                if self.failed_turns >= 2:
                    print("💡 Introducing a new angle to the conversation...")
                    current_message = f"Back to the original topic - {self.original_topic}: What's another angle to consider?"
                    self.failed_turns = 0
                    # Don't increment turn count, just continue to retry
                    continue
                    
                self.turn_count += 1
                continue
            
            # Reset failed turn counter on success
            self.failed_turns = 0
            
            # Remove the trimming - let the model control length
            # The model should follow the "2-3 sentences" instruction
            
            # Agent speaks (pass only the text, not the tuple)
            current_speaker.speak(response)
            
            # Update conversation history with SANITIZED versions
            # Pass only the response text, not the thinking_time
            current_speaker.add_to_history(current_speaker.name, response)
            current_listener.add_to_history(current_speaker.name, response)
            
            # Switch speakers
            current_speaker, current_listener = current_listener, current_speaker
            current_message = response
            
            self.turn_count += 1
        
        print("\n" + "="*60)
        print("CONVERSATION END")
        print("="*60)


def get_user_input():
    """Get conversation parameters from user"""
    print("\n" + "="*60)
    print("AI AGENT CONVERSATION SETUP")
    print("="*60)
    
    # Get topic
    print("\nSuggested topics:")
    print("1. The future of artificial intelligence")
    print("2. Should we colonize Mars?")
    print("3. The impact of social media on society")
    print("4. Climate change and solutions")
    print("5. The role of technology in education")
    print("6. Custom topic")
    
    choice = input("\nChoose a topic (1-6): ").strip()
    
    topics = {
        "1": "What do you think about the future of artificial intelligence?",
        "2": "Should humanity colonize Mars? What are the pros and cons?",
        "3": "How has social media impacted society?",
        "4": "What are the most effective solutions to climate change?",
        "5": "How should technology be used in education?",
    }
    
    if choice == "6":
        topic = input("Enter your custom topic: ").strip()
    else:
        topic = topics.get(choice, topics["1"])
    
    # Get number of turns
    turns_input = input("\nNumber of conversation turns (default 10): ").strip()
    try:
        max_turns = int(turns_input) if turns_input else 10
    except ValueError:
        max_turns = 10
    
    # Voice preferences
    print("\nVoice options:")
    print("1. Guy (Male) & Jenny (Female) - Default")
    print("2. Christopher (Male) & Aria (Female)")
    print("3. Eric (Male) & Sara (Female)")
    print("4. Ryan (British Male) & Sonia (British Female)")
    
    voice_choice = input("\nChoose voice pair (1-4, default 1): ").strip()
    
    voice_pairs = {
        "1": ("en-US-GuyNeural", "en-US-JennyNeural"),
        "2": ("en-US-ChristopherNeural", "en-US-AriaNeural"),
        "3": ("en-US-EricNeural", "en-US-SaraNeural"),
        "4": ("en-GB-RyanNeural", "en-GB-SoniaNeural"),
    }
    
    voices = voice_pairs.get(voice_choice, voice_pairs["1"])
    
    return topic, max_turns, voices


def main():
    """Main function to set up and run the agent conversation"""
    
    # Get user preferences
    topic, max_turns, voices = get_user_input()
    
    print("\n🚀 Initializing AI Agents...")
    
    # Create two agents with clearly distinct roles
    agent1 = Agent(
        name="Alex",
        personality="ROLE: Technical Analyst. You provide concise, technical, analytical responses. Focus on specific tools, frameworks, and implementation details. Example: 'Selenium automates browser testing through WebDriver API.' Keep responses factual and precise. No filler words or emotional language.",
        voice=voices[0]
    )
    
    agent2 = Agent(
        name="Sam",
        personality="ROLE: Strategic Critic. You challenge assumptions, identify limitations, and ask probing questions. Focus on business impact, risks, and real-world constraints. Example: 'What about edge cases that current AI models miss?' Be direct and questioning. No filler words or emotional language.",
        voice=voices[1]
    )
    
    # Create conversation manager
    manager = ConversationManager(agent1, agent2)
    manager.max_turns = max_turns
    
    # Start the conversation
    manager.start_conversation(topic)
    
    print("\n✅ Conversation completed!")
    
    # Ask if user wants another conversation
    again = input("\nStart another conversation? (y/n): ").strip().lower()
    if again == 'y':
        main()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Conversation interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
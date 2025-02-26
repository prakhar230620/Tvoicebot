# tts.py
import re
import threading
import logging
import os
import time
import edge_tts
import asyncio
import pygame
from langdetect import detect
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class InterruptibleTTS:
    def __init__(self):
        self.stop_speaking = threading.Event()
        self.speak_thread = None

    def speak(self, text, voice):
        self.stop_speaking.clear()
        if self.speak_thread and self.speak_thread.is_alive():
            self.stop()
            self.speak_thread.join()

        self.speak_thread = threading.Thread(target=self._speak_thread, args=(text, voice))
        self.speak_thread.start()

    def _speak_thread(self, text, voice):
        try:
            asyncio.run(self._async_speak(text, voice))
        except Exception as e:
            logging.error(f"Error in TTS: {e}")

    async def _async_speak(self, text, voice):
        try:
            communicate = edge_tts.Communicate(text, voice=voice, rate="+22%", pitch="-2Hz", volume="-3%")
            output_file = "temp_output.mp3"
            await communicate.save(output_file)

            pygame.mixer.init()
            pygame.mixer.music.load(output_file)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                if self.stop_speaking.is_set():
                    pygame.mixer.music.stop()
                    break
                time.sleep(0.1)

            pygame.mixer.music.stop()
            pygame.mixer.quit()
            os.remove(output_file)
            logging.info(f"Deleted temporary file: {output_file}")

        except Exception as e:
            logging.error(f"Error in async TTS: {e}")

    def stop(self):
        self.stop_speaking.set()
        if self.speak_thread and self.speak_thread.is_alive():
            self.speak_thread.join()

tts_engine = InterruptibleTTS()

def filter_text(text):
    # Remove emojis
    text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', text)

    # Handle web links
    text = re.sub(r'(https?://\S+)', lambda m: process_web_link(m.group(1)), text)

    # Replace symbols with their spoken equivalents
    symbol_replacements = {
        '*': ' asterisk ',
        '+': ' plus ',
        '-': ' minus ',
        '/': ' divided by ',
        '=': ' equals ',
        '%': ' percent ',
        '&': ' and ',
        '#': ' hash ',
        '@': ' at ',
        '!': ' exclamation mark ',
        '?': ' question mark ',
    }
    for symbol, replacement in symbol_replacements.items():
        text = text.replace(symbol, replacement)

    # Handle code-like patterns and mathematical expressions
    text = re.sub(r'\b\w+\(.*?\)', lambda m: f"function {m.group(0)}", text)
    text = re.sub(r'\b[a-zA-Z_]\w*\b(?=\s*[=+\-*/])', lambda m: f"variable {m.group(0)}", text)
    text = re.sub(r'\b\d+(\.\d+)?\s*[-+*/]\s*\d+(\.\d+)?\b', lambda m: f"expression {m.group(0)}", text)

    return text.strip()

def process_web_link(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace('www.', '')
    path = parsed_url.path.replace('/', ' slash ').strip()
    return f"web link: {domain} {path}"

def detect_language(text):
    try:
        return detect(text)
    except:
        return 'en'  # Default to English if detection fails

def improve_pronunciation(text, lang):
    # Add pronunciation rules
    pronunciation_rules = [
        (r'\bAPI\b', 'A P I'),
        (r'\bSQL\b', 'S Q L'),
        (r'\bGUI\b', 'G U I'),
        (r'\bWiFi\b', 'Wi-Fi'),
        (r'\bUI/UX\b', 'U I U X'),
        (r'\bAI\b', 'A I'),
        (r'\bML\b', 'M L'),
        (r'\bNLP\b', 'N L P'),
        (r'\bIoT\b', 'I o T'),
    ]

    for pattern, replacement in pronunciation_rules:
        text = re.sub(pattern, replacement, text)

    return text

def group_words(text):
    # Define words or phrases that should be spoken together
    grouped_words = [
        r'\b(text to speech)\b',
        r'\b(machine learning)\b',
        r'\b(artificial intelligence)\b',
        r'\b(natural language processing)\b',
        r'\b(user interface)\b',
        r'\b(user experience)\b',
    ]

    for group in grouped_words:
        text = re.sub(group, lambda m: m.group(0).replace(' ', '_'), text)

    return text

def context_aware_replace(text, lang):
    # Define word replacements based on context and language
    word_replacements = {
        'en': {
            'use': {
                'default': 'use',
                'verb': 'use',
                'noun': 'use'
            },
            'madad': {
                'default': 'help',
                'verb': 'help',
                'noun': 'assistance'
            },
            'okay': {
                'default': 'okay',
                'adjective': 'okay',
                'interjection': 'okay'
            }
        },
        'hi': {
            'use': {
                'default': 'इस्तेमाल',
                'verb': 'इस्तेमाल करना',
                'noun': 'उपयोग',
                'name': 'यूज़'
            },
            'madad': {
                'default': 'मदद',
                'verb': 'सहायता करना',
                'noun': 'सहायता'
            },
            'okay': {
                'default': 'ठीक है',
                'adjective': 'ठीक',
                'interjection': 'अच्छा'
            }
        },
        'hinglish': {
            'use': {
                'default': 'use',
                'verb': 'utilize karna',
                'noun': 'upyog',
                'name': 'use'
            },
            'madad': {
                'default': 'madad',
                'verb': 'help karna',
                'noun': 'assistance'
            },
            'okay': {
                'default': 'okay',
                'adjective': 'theek',
                'interjection': 'acha'
            }
        }
    }

    replacements = word_replacements.get(lang, word_replacements['en'])

    def replace_word(match):
        word = match.group(0).lower()
        context = determine_context(match)
        replacement = replacements.get(word, {}).get(context, replacements.get(word, {}).get('default', word))
        return replacement if match.group(0).islower() else replacement.capitalize()

    for word in replacements:
        text = re.sub(r'\b' + word + r'\b', replace_word, text, flags=re.IGNORECASE)

    return text

def determine_context(match):
    prev_words = match.string[max(0, match.start() - 30):match.start()].split()[-3:]
    next_words = match.string[match.end():match.end() + 30].split()[:3]

    if any(word.lower() in ['to', 'will', 'can', 'should', 'must'] for word in prev_words):
        return 'verb'
    elif any(word.lower() in ['of', 'for', 'in', 'with'] for word in next_words):
        return 'noun'
    elif any(word.lower() in ['is', 'was', 'very', 'quite'] for word in prev_words):
        return 'adjective'
    elif not prev_words or prev_words[-1] in ['.', '!', '?']:
        return 'interjection'
    elif any(word.lower() in ['mr', 'mrs', 'ms', 'dr', 'prof'] for word in prev_words):
        return 'name'
    else:
        return 'default'

def detect_hinglish(text):
    # Simple Hinglish detection based on the presence of both English and Hindi words
    english_words = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
    hindi_words = set(re.findall(r'\b[ऀ-ॿ]+\b', text))

    if english_words and hindi_words:
        return 'hinglish'
    elif hindi_words:
        return 'hi'
    else:
        return 'en'

def speak(text):
    try:
        filtered_text = filter_text(text)
        lang = detect_hinglish(filtered_text)
        filtered_text = context_aware_replace(filtered_text, lang)
        filtered_text = improve_pronunciation(filtered_text, lang)
        filtered_text = group_words(filtered_text)

        # Use different voices for English, Hindi, and Hinglish
        if lang == 'en':
            voice = "en-IN-PrabhatNeural"
        elif lang == 'hi':
            voice = "hi-IN-MadhurNeural"
        else:  # Hinglish
            voice = "en-IN-PrabhatNeural"  # Using Indian English voice for Hinglish

        logging.info(f"Assistant speaking ({lang}): {filtered_text}")
        tts_engine.speak(filtered_text, voice)
    except Exception as e:
        logging.error(f"Text-to-speech error: {e}")

# Test the TTS functionality
if __name__ == "__main__":
    test_texts = [
        "Use the pen to write.",
        "मुझे एक pen use करना है।",
        "Mr. Use ne mujhe madad ki.",
        "Kya aap meri madad kar sakte hain?",
        "यह पेन अच्छा use करता है।",
        "Is project me AI ka use kiya gaya hai.",
        "Please visit https://www.example.com for more information.",
        "In ML and AI, we use APIs for NLP tasks.",
    ]

    for test_text in test_texts:
        speak(test_text)
        time.sleep(5)  # Give some time for the speech to complete

    tts_engine.stop()
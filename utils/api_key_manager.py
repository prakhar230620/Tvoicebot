import os
import time
from typing import Optional, Dict
from datetime import datetime, timedelta
from dotenv import load_dotenv
import threading
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIKeyManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super(APIKeyManager, cls).__new__(cls)
                    # Initialize instance attributes here
                    instance.initialized = False
                    instance.api_keys = []
                    instance.key_status = {}
                    instance.current_key_index = 0
                    instance.cooldown_period = 61  # 61 seconds cooldown
                    instance.max_requests_per_minute = 50  # Adjust based on GROQ's actual limit
                    cls._instance = instance
        return cls._instance

    def __init__(self):
        if not self.initialized:
            self.load_api_keys()
            self.initialized = True

    def load_api_keys(self):
        """Load API keys from .env.api file"""
        # Load environment variables from .env.api
        if not os.path.exists('.env.api'):
            raise FileNotFoundError(".env.api file not found")
            
        load_dotenv('.env.api')
        self.api_keys = []
        
        # Load all GROQ API keys (GROQ_API_KEY1, GROQ_API_KEY2, etc.)
        i = 1
        while True:
            key = os.getenv(f'GROQ_API_KEY{i}')
            if not key:
                break
            if key.strip():  # Only add non-empty keys
                self.api_keys.append(key)
                # Initialize key status
                self.key_status[key] = {
                    'requests_count': 0,
                    'last_reset': time.time(),
                    'in_cooldown': False,
                    'cooldown_until': None
                }
            i += 1
        
        if not self.api_keys:
            raise ValueError("No valid GROQ API keys found in .env.api file")
        
        logger.info(f"Loaded {len(self.api_keys)} API keys")

    def reset_key_counter(self, key: str):
        """Reset the request counter for a key"""
        self.key_status[key]['requests_count'] = 0
        self.key_status[key]['last_reset'] = time.time()

    def put_key_in_cooldown(self, key: str):
        """Put a key in cooldown state"""
        self.key_status[key]['in_cooldown'] = True
        self.key_status[key]['cooldown_until'] = time.time() + self.cooldown_period
        logger.info(f"API key put in cooldown until {datetime.fromtimestamp(self.key_status[key]['cooldown_until'])}")

    def check_and_update_cooldown(self, key: str):
        """Check if key can be removed from cooldown"""
        if not self.key_status[key]['in_cooldown']:
            return
        
        if time.time() >= self.key_status[key]['cooldown_until']:
            self.key_status[key]['in_cooldown'] = False
            self.key_status[key]['cooldown_until'] = None
            self.reset_key_counter(key)
            logger.info(f"API key removed from cooldown")

    def get_next_available_key(self) -> Optional[str]:
        """Get the next available API key"""
        if not self.api_keys:
            self.load_api_keys()  # Reload keys if none are available
            
        if not self.api_keys:
            return None
            
        start_index = self.current_key_index
        
        while True:
            # Check current key
            current_key = self.api_keys[self.current_key_index]
            
            # Check and update cooldown status
            self.check_and_update_cooldown(current_key)
            
            # Check if key is available
            if not self.key_status[current_key]['in_cooldown']:
                # Check if we need to reset the counter
                if time.time() - self.key_status[current_key]['last_reset'] >= 60:
                    self.reset_key_counter(current_key)
                
                # Check if key has not exceeded limit
                if self.key_status[current_key]['requests_count'] < self.max_requests_per_minute:
                    return current_key
            
            # Move to next key
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            
            # If we've checked all keys and come back to start, check if any key is usable
            if self.current_key_index == start_index:
                # Find the key that will be available soonest
                soonest_available = float('inf')
                for key in self.api_keys:
                    if self.key_status[key]['in_cooldown']:
                        if self.key_status[key]['cooldown_until'] < soonest_available:
                            soonest_available = self.key_status[key]['cooldown_until']
                
                if soonest_available != float('inf'):
                    # Wait until the soonest key is available
                    wait_time = max(0, soonest_available - time.time())
                    if wait_time > 0:
                        logger.info(f"All keys in cooldown. Waiting {wait_time:.2f} seconds...")
                        time.sleep(wait_time)
                        continue
                
                return None

    def get_api_key(self) -> str:
        """Get an available API key and update its usage"""
        with self._lock:
            key = self.get_next_available_key()
            
            if key is None:
                raise Exception("No API keys available")
            
            # Update usage
            self.key_status[key]['requests_count'] += 1
            
            # Check if key needs to go into cooldown
            if self.key_status[key]['requests_count'] >= self.max_requests_per_minute:
                self.put_key_in_cooldown(key)
            
            return key

    def mark_key_error(self, key: str):
        """Mark a key as having an error (e.g., rate limit exceeded)"""
        with self._lock:
            if key in self.key_status:
                self.put_key_in_cooldown(key)
                logger.warning(f"API key marked as error and put in cooldown")

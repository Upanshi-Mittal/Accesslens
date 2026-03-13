import sys
import os

# Add the backend directory to sys.path
sys.path.append(os.path.abspath(os.curdir))

try:
    from app.core.config import settings
    print("Settings loaded successfully")
    print(f"REDIS_URL: {settings.redis_url}")
    print(f"DATABASE_URL: {settings.database_url}")
    print(f"RATE_LIMIT: {settings.rate_limit_per_minute}")
    print(f"AI_MAX_RETRIES: {settings.ai_max_retries}")
    
    from app.ai.llava_integration import LLaVAService
    from app.ai.mistral_integration import MistralService
    print("AI Services imported successfully")
    
    from app.engines.ai_engine import AIEngine
    print("AI Engine imported successfully")
    
    engine = AIEngine()
    print("AI Engine initialized successfully")
    
except Exception as e:
    print(f"Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

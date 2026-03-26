import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.services.ai_service import ai_service

async def test():
    print("=" * 50)
    print("Testing AI Service...")
    print("=" * 50)
    print(f"OPENAI_API_KEY from env: {os.getenv('OPENAI_API_KEY', 'NOT SET')[:20]}...")
    print(f"AI enabled: {ai_service.enabled}")
    if hasattr(ai_service, 'model'):
        print(f"Model: {ai_service.model}")
    print("-" * 50)
    
    if not ai_service.enabled:
        print("\n❌ AI service is disabled. Check your .env file!")
        print("Make sure OPENAI_API_KEY is set correctly.")
        return
    
    print("\n🔄 Generating summary...")
    
    summary = await ai_service.generate_change_summary(
        old_content="The quick brown fox jumps over the lazy dog.",
        new_content="The quick brown fox jumps over the lazy dog. This is new content added about FreshLense monitoring.",
        page_title="Test Page",
        url="https://example.com"
    )
    
    print("\n" + "=" * 50)
    print("✅ AI Summary Result:")
    print("=" * 50)
    print(f"Summary: {summary.get('summary', 'No summary')}")
    print(f"\nChange Type: {summary.get('change_type', 'unknown')}")
    print(f"Sentiment: {summary.get('sentiment', 'unknown')}")
    print(f"\nKey Changes:")
    for change in summary.get('key_changes', []):
        print(f"  • {change}")
    print(f"\nTechnical Impact: {summary.get('technical_impact', 'N/A')}")
    print(f"Recommendation: {summary.get('recommendation', 'N/A')}")
    print(f"\nModel Used: {summary.get('model_used', 'unknown')}")

asyncio.run(test())
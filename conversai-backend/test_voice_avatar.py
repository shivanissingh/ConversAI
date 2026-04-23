"""
Test Script for Voice & Avatar Engine

Tests voice generation and avatar metadata generation locally.
Run from conversai-backend/ directory:
    python test_voice_avatar.py
"""

import asyncio
from src.engines.voice import synthesize_audio_and_avatar
from src.shared.types import Segment


async def test_voice_engine():
    """Test basic voice generation."""
    print("\n" + "="*60)
    print("TEST 1: Basic Voice Generation (Avatar Disabled)")
    print("="*60)
    
    narration = "Ever wondered how Netflix knows exactly what show you'll binge next? That's machine learning in action—and it's simpler than you think."
    
    try:
        result = await synthesize_audio_and_avatar(
            narration=narration,
            avatar_enabled=False
        )
        
        print(f"✓ Audio generated successfully")
        print(f"  Duration: {result['duration']:.2f}s")
        print(f"  Format: {result['format']}")
        print(f"  Size: {result['metadata']['audioSize']} bytes")
        print(f"  Generation Time: {result['metadata']['generationTime']:.2f}s")
        print(f"  Has Avatar: {result['metadata']['hasAvatar']}")
        print(f"  Audio (first 100 chars): {result['audio'][:100]}...")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")


async def test_voice_avatar_engine():
    """Test voice + avatar metadata generation."""
    print("\n" + "="*60)
    print("TEST 2: Voice + Avatar Generation (Avatar Enabled)")
    print("="*60)
    
    narration = "Ever wondered how Netflix knows exactly what show you'll binge next? That's machine learning in action—and it's simpler than you think. Machine learning is basically teaching computers to learn from examples, just like how you learned to recognize your friends' faces."
    
    segments = [
        Segment(
            text="Ever wondered how Netflix knows exactly what show you'll binge next? That's machine learning in action—and it's simpler than you think.",
            startTime=0.0,
            endTime=9.6
        ),
        Segment(
            text="Machine learning is basically teaching computers to learn from examples, just like how you learned to recognize your friends' faces.",
            startTime=9.6,
            endTime=26.4
        )
    ]
    
    try:
        result = await synthesize_audio_and_avatar(
            narration=narration,
            avatar_enabled=True,
            segments=segments
        )
        
        print(f"✓ Audio + Avatar generated successfully")
        print(f"  Duration: {result['duration']:.2f}s")
        print(f"  Format: {result['format']}")
        print(f"  Size: {result['metadata']['audioSize']} bytes")
        print(f"  Generation Time: {result['metadata']['generationTime']:.2f}s")
        print(f"  Has Avatar: {result['metadata']['hasAvatar']}")
        
        if result['avatar']:
            print(f"\n  Avatar Metadata:")
            print(f"    States: {result['avatar']['metadata']['stateCount']}")
            print(f"    Total Duration: {result['avatar']['metadata']['totalDuration']:.2f}s")
            print(f"    Cues: {len(result['avatar']['cues'])}")
            
            print(f"\n  Avatar States:")
            for i, state in enumerate(result['avatar']['states']):
                print(f"    State {i+1}: {state['startTime']:.1f}s-{state['endTime']:.1f}s | "
                      f"{state['state']} | intensity: {state['intensity']}")
            
            print(f"\n  Animation Cues:")
            for i, cue in enumerate(result['avatar']['cues']):
                print(f"    Cue {i+1}: {cue['timestamp']:.1f}s | {cue['cueType']}")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")


async def test_empty_segments():
    """Test avatar generation with no segments."""
    print("\n" + "="*60)
    print("TEST 3: Avatar with No Segments (Fallback)")
    print("="*60)
    
    narration = "This is a test narration without segments."
    
    try:
        result = await synthesize_audio_and_avatar(
            narration=narration,
            avatar_enabled=True,
            segments=[]
        )
        
        print(f"✓ Audio + Avatar generated successfully (fallback mode)")
        print(f"  Has Avatar: {result['metadata']['hasAvatar']}")
        
        if result['avatar']:
            print(f"  Avatar States: {result['avatar']['metadata']['stateCount']}")
            print(f"  State: {result['avatar']['states'][0]['state']}")
            print(f"  Intensity: {result['avatar']['states'][0]['intensity']}")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")


async def test_validation_error():
    """Test input validation."""
    print("\n" + "="*60)
    print("TEST 4: Input Validation (Empty Narration)")
    print("="*60)
    
    try:
        result = await synthesize_audio_and_avatar(
            narration="",
            avatar_enabled=False
        )
        print(f"✗ Test failed: Should have raised ValidationError")
    except Exception as e:
        print(f"✓ Validation error raised correctly: {e}")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Voice & Avatar Engine - Test Suite")
    print("="*60)
    
    await test_voice_engine()
    await test_voice_avatar_engine()
    await test_empty_segments()
    await test_validation_error()
    
    print("\n" + "="*60)
    print("All tests completed")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

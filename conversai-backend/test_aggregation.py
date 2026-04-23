"""
Test script for Aggregation Engine

This script tests the complete aggregation flow with both
success and failure scenarios.
"""
from dotenv import load_dotenv
load_dotenv()
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.engines.aggregation import aggregate, AggregationError, ValidationError
from src.shared.logger import logger


async def test_successful_aggregation():
    """Test successful aggregation with all engines working."""
    print("\n" + "=" * 80)
    print("TEST 1: Successful Aggregation (Short Duration)")
    print("=" * 80)
    
    try:
        result = await aggregate(
            text="Quantum entanglement is a phenomenon in quantum physics where two particles become interconnected and the quantum state of one instantly influences the other, regardless of the distance between them. Einstein called this 'spooky action at a distance' because it seems to violate the principle that nothing can travel faster than light.",
            duration="short",
            instruction=None,
            avatar_enabled=True
        )
        
        print("\n✓ AGGREGATION SUCCEEDED")
        print(f"  - Narration length: {len(result['narration'])} chars")
        print(f"  - Segments: {len(result['segments'])}")
        print(f"  - Audio duration: {result['audioDuration']:.1f}s")
        print(f"  - Visuals generated: {result['metadata']['visualStats']['generated']}/{result['metadata']['visualStats']['requested']}")
        print(f"  - Avatar: {'Yes' if result['metadata']['avatarSuccess'] else 'No'}")
        print(f"  - Total time: {result['metadata']['totalTime']:.1f}s")
        
        # Show segment details
        print("\n  Segments:")
        for segment in result['segments']:
            has_visual = "✓" if segment.get('visual') else "✗"
            print(f"    {has_visual} {segment['id']}: {segment['startTime']:.1f}s - {segment['endTime']:.1f}s")
        
        return True
        
    except Exception as e:
        print(f"\n✗ AGGREGATION FAILED: {e}")
        return False


async def test_medium_duration():
    """Test aggregation with medium duration."""
    print("\n" + "=" * 80)
    print("TEST 2: Medium Duration with Instruction")
    print("=" * 80)
    
    try:
        result = await aggregate(
            text="Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing algorithms that can access data and use it to learn for themselves. The primary aim is to allow computers to learn automatically without human intervention.",
            duration="medium",
            instruction="Explain like I'm a high school student",
            avatar_enabled=True
        )
        
        print("\n✓ AGGREGATION SUCCEEDED")
        print(f"  - Narration length: {len(result['narration'])} chars")
        print(f"  - Segments: {len(result['segments'])}")
        print(f"  - Audio duration: {result['audioDuration']:.1f}s")
        print(f"  - Total time: {result['metadata']['totalTime']:.1f}s")
        
        return True
        
    except Exception as e:
        print(f"\n✗ AGGREGATION FAILED: {e}")
        return False


async def test_avatar_disabled():
    """Test aggregation with avatar disabled."""
    print("\n" + "=" * 80)
    print("TEST 3: Avatar Disabled")
    print("=" * 80)
    
    try:
        result = await aggregate(
            text="Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes that process information using a connectionist approach to computation.",
            duration="short",
            instruction=None,
            avatar_enabled=False
        )
        
        print("\n✓ AGGREGATION SUCCEEDED")
        print(f"  - Avatar: {'Yes' if result['metadata']['avatarSuccess'] else 'No'}")
        print(f"  - Avatar should be: No")
        
        if result['metadata']['avatarSuccess']:
            print("  ⚠ WARNING: Avatar was generated but should be disabled!")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n✗ AGGREGATION FAILED: {e}")
        return False


async def test_validation_errors():
    """Test input validation errors."""
    print("\n" + "=" * 80)
    print("TEST 4: Input Validation Errors")
    print("=" * 80)
    
    tests_passed = 0
    
    # Test 1: Empty text
    try:
        await aggregate(text="", duration="short")
        print("  ✗ Empty text should raise ValidationError")
    except ValidationError as e:
        print(f"  ✓ Empty text validation: {e}")
        tests_passed += 1
    
    # Test 2: Text too short
    try:
        await aggregate(text="Hi", duration="short")
        print("  ✗ Short text should raise ValidationError")
    except ValidationError as e:
        print(f"  ✓ Short text validation: {e}")
        tests_passed += 1
    
    # Test 3: Invalid duration
    try:
        await aggregate(text="This is a test text that is long enough to pass validation requirements.", duration="invalid")
        print("  ✗ Invalid duration should raise ValidationError")
    except ValidationError as e:
        print(f"  ✓ Invalid duration validation: {e}")
        tests_passed += 1
    
    # Test 4: Instruction too long
    try:
        await aggregate(
            text="This is a test text that is long enough to pass validation requirements.",
            duration="short",
            instruction="x" * 201
        )
        print("  ✗ Long instruction should raise ValidationError")
    except ValidationError as e:
        print(f"  ✓ Long instruction validation: {e}")
        tests_passed += 1
    
    print(f"\n  Validation tests passed: {tests_passed}/4")
    return tests_passed == 4


async def main():
    """Run all test scenarios."""
    print("\n" + "★" * 80)
    print("AGGREGATION ENGINE TEST SUITE")
    print("★" * 80)
    
    results = []
    
    # Run tests
    results.append(await test_successful_aggregation())
    results.append(await test_medium_duration())
    results.append(await test_avatar_disabled())
    results.append(await test_validation_errors())
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

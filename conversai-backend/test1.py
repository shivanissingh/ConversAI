import asyncio
from dotenv import load_dotenv  # Add this
load_dotenv() # Add this - it loads the .env file into os.environ
from src.engines.visual import generate_visuals
from src.shared.types import Segment
async def test():
    segments = [
        Segment(
            text="Imagine a simple network of connected nodes.",
            startTime=0.0,
            endTime=10.0
        )
    ]
    
    metadata = {
        "concepts": ["neural network"],
        "difficulty": "beginner"
    }
    
    print("Generating visual via HF Inference API...")
    result = await generate_visuals(segments, metadata)
    
    print(f"\n✓ Total generated: {result['metadata']['totalGenerated']}")
    print(f"✓ Visual type: {result['visuals'][0]['type']}")
    print(f"✓ Generation time: {result['visuals'][0]['metadata']['generationTime']}s")
    
    # Save image
    import base64
    url = result['visuals'][0]['url']
    if url.startswith('data:image/png'):
        img_data = url.split(',')[1]
        with open('test_image_hf.png', 'wb') as f:
            f.write(base64.b64decode(img_data))
        print("\n✓ Image saved to test_image_hf.png")
asyncio.run(test())
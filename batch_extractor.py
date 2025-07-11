"""
Batch Extractor - Process multiple URLs from the all_links.txt file
"""

import asyncio
import json
from pathlib import Path
from typing import List
import time

from design_extractor import DesignExtractor
from prompt_generator import generate_prompt_from_tokens


async def process_urls_from_file(
    urls_file: Path, 
    output_dir: Path = None,
    max_concurrent: int = 1,  # Set to 1 to avoid browser conflicts
    delay_between_requests: float = 2.0
):
    """Process multiple URLs from a file"""
    
    if not urls_file.exists():
        print(f"❌ URLs file not found: {urls_file}")
        return
    
    # Read URLs
    with open(urls_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    if not urls:
        print("❌ No URLs found in file")
        return
    
    # Add protocol if missing
    processed_urls = []
    for url in urls:
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
        processed_urls.append(url)
    
    print(f"🚀 Processing {len(processed_urls)} URLs...")
    
    # Initialize extractor
    extractor = DesignExtractor(output_dir or "extracted_designs")
    
    # Process URLs sequentially to avoid browser conflicts
    results = []
    
    for url in processed_urls:
        try:
            print(f"🔄 Processing: {url}")
            result = await extractor.extract_design(url)
            
            # Generate prompt
            site_name = result.get('site_name', 'unknown')
            tokens_file = Path(extractor.output_dir) / site_name / "design_tokens.json"
            if tokens_file.exists():
                prompt_file = tokens_file.parent / "recreation_prompt.md"
                generate_prompt_from_tokens(tokens_file, prompt_file)
            
            print(f"✅ Completed: {url}")
            results.append({'url': url, 'status': 'success', 'site_name': site_name})
            
            # Rate limiting between requests
            await asyncio.sleep(delay_between_requests)
            
        except Exception as e:
            print(f"❌ Failed: {url} - {str(e)}")
            results.append({'url': url, 'status': 'failed', 'error': str(e)})
    
    # Summary
    successful = sum(1 for r in results if isinstance(r, dict) and r.get('status') == 'success')
    failed = len(results) - successful
    
    print(f"\n📊 Processing Summary:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📁 Output directory: {extractor.output_dir}")
    
    # Save summary
    summary_file = Path(extractor.output_dir) / "batch_summary.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'total_urls': len(processed_urls),
            'successful': successful,
            'failed': failed,
            'results': results,
            'timestamp': time.time()
        }, f, indent=2)
    
    print(f"📋 Summary saved to: {summary_file}")


async def main():
    """Main execution function"""
    urls_file = Path("links.txt")
    
    if not urls_file.exists():
        print("❌ links.txt not found. Please create it with URLs to process.")
        return
    
    await process_urls_from_file(
        urls_file=urls_file,
        output_dir=Path("extracted_designs"),
        max_concurrent=1,  # Sequential processing to avoid browser conflicts
        delay_between_requests=3.0  # 3 second delay between requests
    )


if __name__ == "__main__":
    asyncio.run(main())
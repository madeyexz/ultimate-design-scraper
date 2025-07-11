#!/usr/bin/env python3
"""
HTML Style Extraction using Google Gemini 2.5 Pro
Processes HTML files and extracts detailed style information for recreation.
"""

import os
import sys
import time
import logging
from pathlib import Path
from PIL import Image
from google import genai
from google.genai.types import HttpOptions

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gemini_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_gemini_client():
    """Initialize the Gemini client with API key from environment variable."""
    logger.info("Setting up Gemini client")
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable not set")
        logger.error("Please set it using: export GEMINI_API_KEY='your_api_key_here'")
        sys.exit(1)
    
    try:
        client = genai.Client(api_key=api_key)
        logger.info("Successfully initialized Gemini client")
        return client
    except Exception as e:
        logger.error(f"Error initializing Gemini client: {e}")
        sys.exit(1)

def read_html_file(file_path):
    """Read HTML file content."""
    logger.debug(f"Reading HTML file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.debug(f"Successfully read {len(content)} characters from {file_path}")
            return content
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

def extract_style_with_gemini(client, html_content, screenshot_path):
    """Extract style information using Gemini 2.5 Pro with both HTML and screenshot."""
    logger.info(f"Extracting style with Gemini using screenshot: {screenshot_path}")
    prompt = f"""Extract the style of this html, use lots of design language to describe it's aesthetic, layout, fonts, interaction, etc. Have so much design detail and technical detail that anyone can recreate this well designed website:

{html_content}
"""
    
    try:
        # Load the screenshot image
        logger.debug(f"Loading screenshot image: {screenshot_path}")
        image = Image.open(screenshot_path)
        logger.debug(f"Image loaded successfully. Size: {image.size}")
        
        # Send both image and HTML content to Gemini
        logger.info("Sending request to Gemini 2.5 Pro")
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[image, prompt],
        )
        logger.info(f"Received response from Gemini. Length: {len(response.text)} characters")
        return response.text
    except Exception as e:
        logger.error(f"Error generating content with Gemini: {e}")
        return None

def save_result(output_path, content):
    """Save the extracted style information to a text file."""
    logger.debug(f"Saving result to: {output_path}")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Successfully saved {len(content)} characters to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving result to {output_path}: {e}")
        return False

def process_html_files():
    """Process all HTML files in the extracted_designs directory."""
    logger.info("Starting HTML processing")
    base_dir = Path(__file__).parent
    input_dir = base_dir / "extracted_designs"
    output_dir = base_dir / "design_prompts"
    
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    
    if not input_dir.exists():
        logger.error(f"Input directory {input_dir} does not exist")
        return
    
    if not output_dir.exists():
        logger.info(f"Creating output directory: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize Gemini client
    client = setup_gemini_client()
    
    # Get all domain folders that contain both page.html and screenshot.png
    logger.info("Scanning for valid domain folders")
    domain_folders = []
    skipped_folders = []
    
    for folder in input_dir.iterdir():
        if folder.is_dir() and not folder.name.startswith('.'):
            html_file = folder / "page.html"
            screenshot_file = folder / "screenshot.png"
            if html_file.exists() and screenshot_file.exists():
                domain_folders.append(folder)
                logger.debug(f"Found valid folder: {folder.name}")
            else:
                skipped_folders.append(folder.name)
                logger.warning(f"Skipping {folder.name} - missing page.html or screenshot.png")
    
    if skipped_folders:
        logger.info(f"Skipped folders: {', '.join(skipped_folders)}")
    
    if not domain_folders:
        logger.error(f"No valid domain folders found in {input_dir}")
        return
    
    logger.info(f"Found {len(domain_folders)} domain folders to process")
    logger.info(f"Processing domains: {[f.name for f in domain_folders]}")
    
    for i, domain_folder in enumerate(domain_folders, 1):
        domain_name = domain_folder.name
        logger.info(f"Processing {i}/{len(domain_folders)}: {domain_name}")
        
        html_file = domain_folder / "page.html"
        screenshot_file = domain_folder / "screenshot.png"
        
        # Read HTML content
        html_content = read_html_file(html_file)
        if not html_content:
            logger.error(f"Skipping {domain_name} due to HTML read error")
            continue
        
        # Extract style with Gemini using both HTML and screenshot
        style_analysis = extract_style_with_gemini(client, html_content, screenshot_file)
        if not style_analysis:
            logger.error(f"Skipping {domain_name} due to Gemini API error")
            continue
        
        # Save result
        output_file = output_dir / f"{domain_name}.txt"
        if save_result(output_file, style_analysis):
            logger.info(f"✓ Saved style analysis to {output_file}")
        else:
            logger.error(f"✗ Failed to save {output_file}")
        
        # Wait 1 minute between requests (except for the last file)
        if i < len(domain_folders):
            logger.info("⏰ Waiting 1 minute before next request...")
            time.sleep(60)
    
    logger.info(f"Processing complete! Results saved in {output_dir}")
    logger.info(f"Total domains processed: {len(domain_folders)}")

if __name__ == "__main__":
    logger.info("Starting Gemini HTML Style Extraction")
    try:
        process_html_files()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        logger.info("Script execution completed")
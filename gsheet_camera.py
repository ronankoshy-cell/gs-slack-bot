import os
import sys
import time
from playwright.sync_api import sync_playwright
from slack_sdk import WebClient
from PIL import Image, ImageChops

# 1. Setup Environment Variables
slack_token = os.environ.get('SLACK_TOKEN')
target_channel = os.environ.get('GROWTH_CHANNEL_ID')

# Paste your "Publish to web" URL here
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTM1euZymtjxn03QmcF-sHQBcjw0SaLhUP6vOgXEFILWdIibeEdjgqAUBF6pwqZbNEKOpf6Z0GzXj2D/pubhtml?gid=594728950&single=true"

# Automatically inject Google's hidden parameters to remove the top header and bottom tabs
if "&chrome=false" not in SHEET_URL:
    SHEET_URL += "&chrome=false&widget=false&headers=false"

client = WebClient(token=slack_token)

def crop_whitespace(image_path):
    """Automatically finds the table and crops out all the empty white space."""
    print("Auto-cropping whitespace...")
    im = Image.open(image_path)
    
    # Convert to standard RGB to prevent transparency issues
    rgb_im = im.convert('RGB')
    
    # Create a perfectly white background to compare against
    bg = Image.new('RGB', rgb_im.size, (255, 255, 255))
    diff = ImageChops.difference(rgb_im, bg)
    
    # Find the exact bounding box of the table (non-white pixels)
    bbox = diff.getbbox()
    
    if bbox:
        # Add a clean 15-pixel white border around the table for aesthetics
        padded_bbox = (
            max(bbox[0] - 15, 0),
            max(bbox[1] - 15, 0),
            min(bbox[2] + 15, im.size[0]),
            min(bbox[3] + 15, im.size[1])
        )
        cropped_im = im.crop(padded_bbox)
        cropped_im.save(image_path)
        print("Cropping successful!")

def take_screenshot_and_send():
    try:
        print("--- GSheets Headless Camera ---")
        png_filename = "exact_cells_snapshot.png"

        # 2. Fire up the headless browser and take the full-page picture
        print("Opening browser...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1200, 'height': 800})
            page = context.new_page()
            
            print("Navigating to clean URL...")
            page.goto(SHEET_URL)
            
            print("Waiting 5 seconds for cells to render...")
            page.wait_for_timeout(5000)
            
            print("Taking raw snapshot...")
            page.screenshot(path=png_filename, full_page=True)
            
            browser.close()

        # 3. Trim the whitespace from the raw screenshot
        crop_whitespace(png_filename)

        # 4. Upload the perfectly cropped PNG to Slack
        print("Uploading PNG to Slack...")
        client.files_upload_v2(
            channel=target_channel,
            file=png_filename,
            title="Google Sheets Exact Snapshot",
            initial_comment="📊 Hi Team, here is the latest CM Summary."
        )
        print("SUCCESS: Clean Google Sheets PNG relayed to target channel.")
        
        time.sleep(3) # Slack API protection
        if os.path.exists(png_filename):
            os.remove(png_filename)
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    take_screenshot_and_send()

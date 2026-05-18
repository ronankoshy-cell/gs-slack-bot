import os
import sys
import time
from playwright.sync_api import sync_playwright
from slack_sdk import WebClient
from PIL import Image, ImageChops

# 1. Setup Environment Variables
slack_token = os.environ.get('SLACK_TOKEN')
target_channel = os.environ.get('GROWTH_CHANNEL_ID')

# 2. Your Multi-Table Task List
# I have kept your original URL for the CM_Summary. 
# Just paste your second URL below!
REPORTS = {
    "CM_Summary": {
        "url": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTM1euZymtjxn03QmcF-sHQBcjw0SaLhUP6vOgXEFILWdIibeEdjgqAUBF6pwqZbNEKOpf6Z0GzXj2D/pubhtml?gid=594728950&single=true",
        "title": "Google Sheets Exact Snapshot - CM Summary",
        "message": "📊 Hi Team, here is the latest CM Summary."
    },
    "Second_Report": {
        "url": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTM1euZymtjxn03QmcF-sHQBcjw0SaLhUP6vOgXEFILWdIibeEdjgqAUBF6pwqZbNEKOpf6Z0GzXj2D/pubhtml?gid=943397354&single=true",
        "title": "Google Sheets Exact Snapshot - Second Report",
        "message": "📊 Hi Team, PFB MTD CM Summary"
    }
}

client = WebClient(token=slack_token)

def crop_whitespace(image_path):
    """Automatically finds the table and crops out all the empty white space."""
    print(f"Auto-cropping whitespace for {image_path}...")
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

def take_screenshots_and_send():
    try:
        print("--- GSheets Headless Camera (Multi-URL) ---")

        # 3. Fire up the headless browser
        print("Opening browser...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1200, 'height': 800})
            page = context.new_page()
            
            # Loop through every table in your REPORTS list
            for report_name, data in REPORTS.items():
                print(f"\n--- Processing {report_name} ---")
                
                # Automatically inject Google's hidden parameters to clean the UI
                target_url = data["url"]
                if "&chrome=false" not in target_url:
                    target_url += "&chrome=false&widget=false&headers=false"

                png_filename = f"{report_name}_snapshot.png"
                
                print("Navigating to clean URL...")
                page.goto(target_url)
                
                print("Waiting 5 seconds for cells to render...")
                page.wait_for_timeout(5000)
                
                print("Taking raw snapshot...")
                page.screenshot(path=png_filename, full_page=True)
                
                # Trim the whitespace from the raw screenshot
                crop_whitespace(png_filename)

                # Upload the perfectly cropped PNG to Slack
                print(f"Uploading {report_name} PNG to Slack...")
                client.files_upload_v2(
                    channel=target_channel,
                    file=png_filename,
                    title=data["title"],
                    initial_comment=data["message"]
                )
                print(f"SUCCESS: Clean Google Sheets PNG relayed to target channel.")
                
                # The crucial 3-second delay to prevent Slack API protection triggers
                time.sleep(3) 
                
                # Delete the image before moving to the next report
                if os.path.exists(png_filename):
                    os.remove(png_filename)
                    
            browser.close()
            print("\nAll snapshots captured and sent successfully!")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    take_screenshots_and_send()

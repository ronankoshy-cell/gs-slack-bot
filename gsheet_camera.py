import os
import sys
import time
from playwright.sync_api import sync_playwright
from slack_sdk import WebClient

# 1. Setup Environment Variables
slack_token = os.environ.get('SLACK_TOKEN')
target_channel = os.environ.get('GROWTH_CHANNEL_ID')

# Paste your "Publish to web" URL here
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTM1euZymtjxn03QmcF-sHQBcjw0SaLhUP6vOgXEFILWdIibeEdjgqAUBF6pwqZbNEKOpf6Z0GzXj2D/pubhtml?gid=594728950&single=true"

client = WebClient(token=slack_token)

def take_screenshot_and_send():
    try:
        print("--- GSheets Headless Camera ---")
        png_filename = "exact_cells_snapshot.png"

        # 2. Fire up the headless browser and take the picture
        print("Opening browser...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            # Set a standard window size so we don't capture massive amounts of empty white space
            context = browser.new_context(viewport={'width': 800, 'height': 600})
            page = context.new_page()
            
            print("Navigating to URL...")
            page.goto(SHEET_URL)
            
            # Wait a full 5 seconds to guarantee Google is completely done drawing the screen
            print("Waiting 5 seconds for cells to render...")
            page.wait_for_timeout(5000)
            
            # Take a full photograph of the webpage—no locators, no searching!
            print("Taking full page snapshot...")
            page.screenshot(path=png_filename, full_page=True)
            
            browser.close()
            print("Screenshot captured successfully!")

        # 3. Upload the PNG to Slack
        print("Uploading PNG to Slack...")
        client.files_upload_v2(
            channel=target_channel,
            file=png_filename,
            title="Google Sheets Exact Snapshot",
            initial_comment="📊 Hi Team, Sharing the CM View."
        )
        print("SUCCESS: Google Sheets PNG relayed to target channel.")
        
        time.sleep(3) # Slack API protection
        if os.path.exists(png_filename):
            os.remove(png_filename)
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    take_screenshot_and_send()

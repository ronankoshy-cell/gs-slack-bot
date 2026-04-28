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
            page = browser.new_page()
            
            # Go to the published sheet
            page.goto(SHEET_URL)
            
            # Wait for the table to load, then take a screenshot of JUST the table element
            page.wait_for_selector("table.waffle")
            page.locator("table.waffle").screenshot(path=png_filename)
            
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
        os.remove(png_filename)
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    take_screenshot_and_send()

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
import re

# 1. Setup Streamlit Page
st.set_page_config(page_title="Kids Bank Card", page_icon="💰")
st.title("💰 Kids Bank Card Generator")

# 2. Connect to Google Sheets using Streamlit Secrets
# (We will set these secrets in Step 3)
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
gc = gspread.authorize(creds)

# Open your sheet
sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1IiFdAUJrcKRuxREGMkn7ejWv395UZJtVIoekk8bVx50/edit')
worksheet = sh.sheet1
def generate_bmp():
    # 1. Image Settings (High Res)
    width, height = 800, 480
    img = Image.new('1', (width, height), 255) # 1-bit B&W
    draw = ImageDraw.Draw(img)
    
    # 2. Fetch Data
    try:
        raw_val = worksheet.acell('F1').value
        clean_val = re.sub(r'[^\d.]', '', raw_val)
        total_balance = float(clean_val)
    except:
        total_balance = 0.0

    # 3. HEADER
    draw.rectangle([0, 0, 800, 60], fill=0)
    # Using default font, but at 800x480 you can draw larger by 'scaling' 
    # if you don't have a custom TTF font file uploaded to GitHub.
    draw.text((20, 15), "MY HOME BANK • LEO'S CARD", fill=1)

    # 4. TOP SECTION: BALANCE
    # We simulate a large font by drawing a bit thicker or using a larger size
    draw.text((50, 80), f"${total_balance:.2f}", fill=0)
    draw.text((50, 160), "TOTAL AVAILABLE", fill=0)
    
    # Draw simple +/- icons on the right
    draw.ellipse([600, 80, 720, 200], outline=0, width=5)
    draw.line([630, 140, 690, 140], fill=0, width=8) # Minus
    draw.line([660, 110, 660, 170], fill=0, width=8) # Plus

    # 5. MIDDLE SECTION: RECENT ACTIVITY
    draw.line([40, 230, 760, 230], fill=0, width=3) # Divider
    draw.text((50, 250), "Recent Activity", fill=0)
    
    data = worksheet.get_all_records()
    recent_tx = data[-3:] # Get last 3
    
    y_pos = 290
    for tx in recent_tx:
        # Assumes columns: Type, Amount, Description
        t_type = tx.get('Type', '+')
        t_amt = tx.get('Amount', '0')
        t_desc = tx.get('Description', 'Chore')
        
        draw.text((50, y_pos), f"{t_type}${t_amt} • {t_desc}", fill=0)
        y_pos += 40

    # 6. BOTTOM SECTION: SAVINGS GOAL
    goal_name = "New Bike"
    goal_target = 100.0
    progress = min(total_balance / goal_target, 1.0)
    
    draw.text((50, 410), f"Saving for: {goal_name}", fill=0)
    draw.text((550, 410), f"{int(progress*100)}% to my Bike!", fill=0)
    
    # Progress Bar Background
    draw.rectangle([50, 440, 750, 465], outline=0, width=3)
    # Progress Fill
    fill_width = int(700 * progress)
    if fill_width > 4:
        draw.rectangle([54, 444, 50 + fill_width, 461], fill=0)

    # 7. Final Polish
    img.save("transfer.bmp")
    return img

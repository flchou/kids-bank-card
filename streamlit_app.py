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
    # 1. Canvas Setup (High Res 800x480)
    width, height = 800, 480
    img = Image.new('1', (width, height), 255) 
    draw = ImageDraw.Draw(img)
    
    # 2. Load Fonts (Ensure the filename matches your uploaded file exactly)
    font_path = "Roboto-VariableFont_wdth,wght.ttf"
    try:
        font_header = ImageFont.truetype(font_path, 35)
        font_balance = ImageFont.truetype(font_path, 140)
        font_sub = ImageFont.truetype(font_path, 30)
        font_activity = ImageFont.truetype(font_path, 32)
        font_goal = ImageFont.truetype(font_path, 28)
    except:
        st.error("Font file not found. Ensure it is in the same folder as this script.")
        return None

    # 3. Data Fetch
    raw_val = worksheet.acell('F1').value
    clean_val = re.sub(r'[^\d.]', '', raw_val)
    total_balance = float(clean_val)
    
    # 4. HEADER (Black bar with white text)
    draw.rectangle([0, 0, 800, 65], fill=0)
    draw.text((400, 32), "MY HOME BANK • LEO'S CARD", fill=1, font=font_header, anchor="mm")

    # 5. BALANCE SECTION
    # Large centered balance
    draw.text((400, 160), f"${total_balance:.2f}", fill=0, font=font_balance, anchor="mm")
    draw.text((400, 245), "TOTAL AVAILABLE", fill=0, font=font_sub, anchor="mm")
    
    # Simple Icons (Centered relative to the text)
    # Plus/Minus circles
    draw.ellipse([620, 110, 710, 200], outline=0, width=4)
    draw.line([640, 155, 690, 155], fill=0, width=6) # Minus
    draw.line([665, 130, 665, 180], fill=0, width=6) # Plus

    # 6. RECENT ACTIVITY (3 rows)
    draw.line([50, 280, 750, 280], fill=0, width=2)
    draw.text((60, 300), "Recent Activity", fill=0, font=font_activity)
    
    data = worksheet.get_all_records()
    recent_tx = data[-3:] # Last 3 items
    
    y_off = 345
    for tx in recent_tx:
        t_type = tx.get('Type', '+')
        t_amt = tx.get('Amount', '0')
        t_desc = tx.get('Description', 'Chore')
        
        # Draw transaction line
        draw.text((60, y_off), f"{t_type}${t_amt}", fill=0, font=font_activity)
        draw.text((180, y_off), f"• {t_desc}", fill=0, font=font_activity)
        y_off += 40

    # 7. GOAL SECTION (Bottom)
    goal_target = 100.0
    progress_pct = min(total_balance / goal_target, 1.0)
    
    draw.text((60, 440), "Saving for: New Bike", fill=0, font=font_goal, anchor="lm")
    draw.text((740, 440), f"{int(progress_pct*100)}% of $100.00", fill=0, font=font_goal, anchor="rm")
    
    # Progress Bar (Modern pill shape)
    bar_coords = [250, 430, 550, 450]
    draw.rectangle(bar_coords, outline=0, width=2)
    fill_end = bar_coords[0] + (300 * progress_pct)
    draw.rectangle([bar_coords[0]+4, bar_coords[1]+4, fill_end-4, bar_coords[3]-4], fill=0)

    # 8. Save
    img.save("transfer.bmp")
    return img

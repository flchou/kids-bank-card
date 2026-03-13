import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image, ImageDraw, ImageFont
import re
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Kids Bank Card Sync", page_icon="💰")
st.title("💰 Kids Bank Card Sync")
st.markdown("Update your Google Sheet, then click the button below to generate the new card image.")

# 2. Google Sheets Authentication
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

try:
    # Pulls from the Secrets tab in Streamlit Cloud settings
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)

    # Use the Direct URL for reliability
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1IiFdAUJrcKRuxREGMkn7ejWv395UZJtVIoekk8bVx50/edit"
    sh = gc.open_by_url(SHEET_URL)
    worksheet = sh.sheet1
except Exception as e:
    st.error(f"Authentication Error: {e}")
    st.stop()

# --- (Keep your page config and authentication code at the top as is) ---

def generate_bmp():
    # --- Canvas Setup (High Res 800x480) ---
    width, height = 800, 480
    img = Image.new('1', (width, height), 255) 
    draw = ImageDraw.Draw(img)
    
    # --- Font Loading with UPDATED SIZES ---
    font_path = "Roboto-VariableFont_wdth,wght.ttf"
    try:
        font_header = ImageFont.truetype(font_path, 32)
        font_timestamp = ImageFont.truetype(font_path, 20)
        font_balance = ImageFont.truetype(font_path, 140)
        font_sub = ImageFont.truetype(font_path, 30)
        
        # FIXED: Reduced these sizes to prevent overlap
        font_activity_hd = ImageFont.truetype(font_path, 24) # Shrank from 32
        font_date = ImageFont.truetype(font_path, 22)       # Shrank from 26
        font_activity = ImageFont.truetype(font_path, 26)   # Shrank from 32
        font_goal = ImageFont.truetype(font_path, 24)       # Shrank from 28
    except:
        st.error("Font file not found. Ensure the .ttf file is in your GitHub repo.")
        return None

    # --- Data Fetching ---
    try:
        raw_val = worksheet.acell('F1').value
        clean_val = re.sub(r'[^\d.]', '', raw_val)
        total_balance = float(clean_val)
        
        all_data = worksheet.get_all_records()
        recent_tx = all_data[-3:] if len(all_data) >= 3 else all_data
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        total_balance = 0.0
        recent_tx = []

    # --- UI DRAWING ---

    # 1. HEADER (Remains the same)
    draw.rectangle([0, 0, 800, 70], fill=0)
    draw.text((40, 35), "MY HOME BANK • LEO'S CARD", fill=1, font=font_header, anchor="lm")
    now = datetime.now().strftime("%b %d, %H:%M")
    draw.text((760, 35), f"Updated: {now}", fill=1, font=font_timestamp, anchor="rm")

    # 2. BALANCE SECTION (Remains the same)
    draw.text((400, 165), f"${total_balance:.2f}", fill=0, font=font_balance, anchor="mm")
    draw.text((400, 245), "TOTAL AVAILABLE", fill=0, font=font_sub, anchor="mm")
    
    # Plus Icons
    draw.ellipse([620, 110, 710, 200], outline=0, width=4)
    draw.line([640, 155, 690, 155], fill=0, width=6)
    draw.line([665, 130, 665, 180], fill=0, width=6)

    # 3. RECENT ACTIVITY (Updated Spacing and Fonts)
    draw.line([50, 285, 750, 285], fill=0, width=2)
    
    # FIXED: Used smaller header font
    draw.text((60, 305), "Recent Activity", fill=0, font=font_activity_hd)
    
    # FIXED: Increased initial y_off and row spacing
    y_off = 345 
    for tx in recent_tx:
        # Clean up date string
        t_date = str(tx.get('Date', ''))[:10] 
        t_type = tx.get('Type', '+')
        t_amt = tx.get('Amount', '0')
        t_desc = tx.get('Description', 'Chore')
        
        # FIXED: Used smaller fonts for all elements
        draw.text((60, y_off), t_date, fill=0, font=font_date)
        draw.text((220, y_off), f"{t_type}${t_amt}", fill=0, font=font_activity)
        draw.text((360, y_off), f"• {t_desc}", fill=0, font=font_activity)
        
        # FIXED: Increased vertical space between rows
        y_off += 45 

    # 4. GOAL SECTION (Pushed Down)
    goal_target = 100.0
    progress_pct = min(total_balance / goal_target, 1.0)
    
    # FIXED: Pushed entire section down to y=440 and used smaller font
    draw.text((60, 440), "Saving for: New Bike", fill=0, font=font_goal, anchor="lm")
    draw.text((740, 440), f"{int(progress_pct*100)}% of $100.00", fill=0, font=font_goal, anchor="rm")
    
    # Progress Bar (Pushed down accordingly)
    bar_coords = [250, 432, 550, 452]
    draw.rectangle(bar_coords, outline=0, width=2)
    fill_end = bar_coords[0] + (300 * progress_pct)
    if progress_pct > 0.02:
        draw.rectangle([bar_coords[0]+4, bar_coords[1]+4, fill_end-4, bar_coords[3]-4], fill=0)

    # --- SAVE ---
    img.save("transfer.bmp")
    return img

# --- (Keep your Streamlit UI logic at the bottom as is) ---

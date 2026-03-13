import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image, ImageDraw, ImageFont
import re
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Time Credit Tracker", page_icon="⏳")
st.title("⏳ Time Credit Sync")

# 2. Google Sheets Authentication
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1IiFdAUJrcKRuxREGMkn7ejWv395UZJtVIoekk8bVx50/edit"
    sh = gc.open_by_url(SHEET_URL)
except Exception as e:
    st.error(f"Authentication Error: {e}")
    st.stop()

def generate_time_bmp(worksheet, name):
    # --- ROTATED CANVAS (176x264) ---
    width, height = 176, 264
    img = Image.new('1', (width, height), 255) 
    draw = ImageDraw.Draw(img)
    
    font_path = "Roboto-VariableFont_wdth,wght.ttf"
    try:
        font_header = ImageFont.truetype(font_path, 16)
        font_time_val = ImageFont.truetype(font_path, 42)
        font_unit = ImageFont.truetype(font_path, 14)
        font_label = ImageFont.truetype(font_path, 12)
        font_row = ImageFont.truetype(font_path, 11)
        font_goal = ImageFont.truetype(font_path, 10)
    except:
        st.error("Font error. Check .ttf file.")
        return None

    # --- Data Fetching ---
    try:
        raw_val = worksheet.acell('F1').value
        # Use regex to keep numbers/decimals (e.g., "5.5 hrs" -> 5.5)
        time_val = re.sub(r'[^\d.]', '', str(raw_val))
        
        goal_name = worksheet.acell('H1').value or "Reward"
        goal_target = float(re.sub(r'[^\d.]', '', str(worksheet.acell('I1').value)))
        
        all_data = worksheet.get_all_records()
        recent_tx = all_data[-3:] # Show 3 rows since we have vertical room
    except:
        time_val, goal_name, goal_target, recent_tx = "0", "Goal", 10.0, []

    # --- UI DRAWING (VERTICAL) ---

    # 1. HEADER BAR
    draw.rectangle([0, 0, 176, 25], fill=0)
    draw.text((88, 12), f"{name.upper()}'S TIME", fill=1, font=font_header, anchor="mm")

    # 2. MAIN TIME DISPLAY
    draw.text((88, 65), f"{time_val}", fill=0, font=font_time_val, anchor="mm")
    draw.text((88, 95), "HOURS REMAINING", fill=0, font=font_unit, anchor="mm")

    # 3. ACTIVITY LOG
    draw.line([10, 115, 166, 115], fill=0, width=1)
    draw.text((15, 125), "Recent Logs", fill=0, font=font_label)
    
    y_off = 145
    for tx in recent_tx:
        # Assumes: Type (+/-), Amount, Description
        t_amt = f"{tx.get('Type', '')}{tx.get('Amount', '0')}h"
        t_desc = str(tx.get('Description', ''))[:14]
        
        draw.text((15, y_off), t_amt, fill=0, font=font_row)
        draw.text((60, y_off), f"• {t_desc}", fill=0, font=font_row)
        y_off += 18

    # 4. REWARD GOAL (Bottom)
    draw.line([10, 215, 166, 215], fill=0, width=1)
    
    # Progress Calculation
    try:
        progress = min(float(time_val) / goal_target, 1.0)
    except: progress = 0
    
    draw.text((15, 230), f"For: {goal_name}", fill=0, font=font_goal)
    
    # Vertical-friendly progress bar
    bar_coords = [15, 240, 161, 250]
    draw.rectangle(bar_coords, outline=0, width=1)
    fill_w = int((bar_coords[2] - bar_coords[0]) * progress)
    if fill_w > 4:
        draw.rectangle([bar_coords[0]+2, bar_coords[1]+2, bar_coords[0]+fill_w-2, bar_coords[3]-2], fill=0)
    
    draw.text((88, 258), f"{int(progress*100)}% to Reward", fill=0, font=font_goal, anchor="mm")

    filename = f"{name.lower()}_time.bmp"
    img.save(filename)
    return filename

# --- TABS ---
tab_k, tab_e = st.tabs(["Kayden's Time", "Ethan's Time"])

with tab_k:
    if st.button('🔄 Sync Kayden Time'):
        ws = sh.worksheet("Kayden")
        fname = generate_time_bmp(ws, "Kayden")
        if fname:
            st.image(fname, width=176) # Preview shows the 90-degree rotation
            with open(fname, "rb") as f:
                st.download_button("📥 Download BMP", f, file_name=fname)

with tab_e:
    if st.button('🔄 Sync Ethan Time'):
        ws = sh.worksheet("Ethan")
        fname = generate_time_bmp(ws, "Ethan")
        if fname:
            st.image(fname, width=176)
            with open(fname, "rb") as f:
                st.download_button("📥 Download BMP", f, file_name=fname)

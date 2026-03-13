import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image, ImageDraw, ImageFont
import re
from datetime import datetime

# --- Auth & Config (Keeping your existing setup) ---
st.set_page_config(page_title="Time Credit Tracker", page_icon="⏳")
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
gc = gspread.authorize(creds)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1IiFdAUJrcKRuxREGMkn7ejWv395UZJtVIoekk8bVx50/edit"
sh = gc.open_by_url(SHEET_URL)

def format_time(val):
    try:
        total_minutes = int(float(val) * 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}h {minutes:02d}m" if hours > 0 else f"{minutes}m"
    except: return "0m"

def generate_time_bmp(worksheet, name):
    # --- Canvas (176x264) ---
    width, height = 176, 264
    img = Image.new('1', (width, height), 255) 
    draw = ImageDraw.Draw(img)
    font_path = "Roboto-VariableFont_wdth,wght.ttf"
    
    try:
        font_header = ImageFont.truetype(font_path, 16)
        font_time_val = ImageFont.truetype(font_path, 34)
        font_sub = ImageFont.truetype(font_path, 11)
        font_stats = ImageFont.truetype(font_path, 12)
        font_row = ImageFont.truetype(font_path, 11)
        font_goal = ImageFont.truetype(font_path, 10)
    except: return None

    # --- Data Fetching & Calculations ---
    all_data = worksheet.get_all_records()
    raw_val = worksheet.acell('F1').value
    total_time_str = format_time(re.sub(r'[^\d.]', '', str(raw_val)))
    
    # Calculate Earned vs Used from the last 10 entries for a "recent" summary
    recent_all = all_data[-10:]
    total_earned = sum(float(re.sub(r'[^\d.]', '', str(x.get('Amount', 0)))) for x in recent_all if x.get('Type') == '+')
    total_used = sum(float(re.sub(r'[^\d.]', '', str(x.get('Amount', 0)))) for x in recent_all if x.get('Type') == '-')

    # --- UI DRAWING ---

    # 1. HEADER
    draw.rectangle([0, 0, 176, 25], fill=0)
    draw.text((88, 12), f"{name.upper()}'S PASS", fill=1, font=font_header, anchor="mm")

    # 2. MAIN BALANCE
    draw.text((88, 60), total_time_str, fill=0, font=font_time_val, anchor="mm")
    draw.text((88, 85), "REMAINING", fill=0, font=font_sub, anchor="mm")

    # 3. EARNED vs USED INDICATORS (New Section)
    draw.rectangle([15, 100, 161, 125], outline=0)
    draw.line([88, 100, 88, 125], fill=0) # Middle Divider
    # Earned (Left)
    draw.text((51, 105), "EARNED", fill=0, font=font_goal, anchor="mm")
    draw.text((51, 117), f"+{format_time(total_earned)}", fill=0, font=font_stats, anchor="mm")
    # Used (Right)
    draw.text((125, 105), "USED", fill=0, font=font_goal, anchor="mm")
    draw.text((125, 117), f"-{format_time(total_used)}", fill=0, font=font_stats, anchor="mm")

    # 4. RECENT LOGS
    draw.text((15, 138), "Activity History", fill=0, font=font_stats)
    y_off = 158
    for tx in all_data[-4:]: # Show 4 rows
        t_type = tx.get('Type', '+')
        t_amt = format_time(re.sub(r'[^\d.]', '', str(tx.get('Amount', '0'))))
        t_desc = str(tx.get('Description', ''))[:12]
        
        # Circle indicator for +/-
        draw.ellipse([15, y_off, 25, y_off+10], outline=0)
        draw.text((20, y_off+5), t_type, fill=0, font=font_goal, anchor="mm")
        
        draw.text((32, y_off+5), f"{t_amt}", fill=0, font=font_row, anchor="lm")
        draw.text((85, y_off+5), f"• {t_desc}", fill=0, font=font_row, anchor="lm")
        y_off += 18

    # 5. PROGRESS BAR (Footer)
    goal_name = worksheet.acell('H1').value or "Reward"
    goal_target = float(re.sub(r'[^\d.]', '', str(worksheet.acell('I1').value or 10)))
    progress = min(float(re.sub(r'[^\d.]', '', str(raw_val or 0))) / goal_target, 1.0)
    
    draw.line([15, 235, 161, 235], fill=0)
    draw.text((88, 243), f"Goal: {goal_name}", fill=0, font=font_goal, anchor="mm")
    draw.rectangle([15, 250, 161, 258], outline=0)
    fill_w = int(146 * progress)
    if fill_w > 4:
        draw.rectangle([17, 252, 15 + fill_w, 256], fill=0)

    filename = f"{name.lower()}_time.bmp"
    img.save(filename)
    return filename

# --- Streamlit Tabs (Keep your Kayden/Ethan Tabs here) ---
tab_k, tab_e = st.tabs(["Kayden", "Ethan"])
with tab_k:
    if st.button('🔄 Sync Kayden'):
        ws = sh.worksheet("Kayden")
        fname = generate_time_bmp(ws, "Kayden")
        st.image(fname, width=176)
        with open(fname, "rb") as f: st.download_button("Download", f, fname)
with tab_e:
    if st.button('🔄 Sync Ethan'):
        ws = sh.worksheet("Ethan")
        fname = generate_time_bmp(ws, "Ethan")
        st.image(fname, width=176)
        with open(fname, "rb") as f: st.download_button("Download", f, fname)

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image, ImageDraw, ImageFont
import re
from datetime import datetime

# --- Auth & Setup ---
# (Keep your existing gspread and streamlit secrets setup here)
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

def generate_pro_bmp(worksheet, name):
    width, height = 176, 264
    # Create a 1-bit image (Black and White only, no grays)
    img = Image.new('1', (width, height), 255) 
    draw = ImageDraw.Draw(img)
    font_path = "Roboto-VariableFont_wdth,wght.ttf"

    try:
        f_name = ImageFont.truetype(font_path, 18)
        f_balance = ImageFont.truetype(font_path, 36) # Shrunk slightly to keep lines thin
        f_label = ImageFont.truetype(font_path, 11)
        f_section = ImageFont.truetype(font_path, 13)
        f_row_time = ImageFont.truetype(font_path, 12) # Shrunk to 12 for sharper rendering
        f_row_desc = ImageFont.truetype(font_path, 10)
        f_sync = ImageFont.truetype(font_path, 9)
    except: return None

    # Data Fetching
    raw_val = worksheet.acell('F1').value
    clean_val = re.sub(r'[^\d.]', '', str(raw_val))
    time_display = format_time(clean_val)
    all_data = worksheet.get_all_records()
    recent_tx = all_data[-5:] 

    # 1. HEADER
    draw.rectangle([0, 0, 176, 30], fill=0)
    draw.text((88, 15), f"{name.upper()} PASS", fill=1, font=f_name, anchor="mm")

    # 2. BALANCE BOX (1px width is cleaner on E-ink)
    draw.rectangle([10, 38, 166, 100], outline=0, width=1)
    draw.text((88, 62), time_display, fill=0, font=f_balance, anchor="mm")
    draw.text((88, 88), "REMAINING BALANCE", fill=0, font=f_label, anchor="mm")

    # 3. SECTION HEADER
    draw.rectangle([10, 110, 166, 127], fill=0)
    draw.text((88, 118), "RECENT ACTIVITY", fill=1, font=f_section, anchor="mm")

    # 4. CUSTOM DRAWN INDICATORS & LOGS
    COL_BRACKET = 8
    COL_TIME = 38
    COL_DESC = 92
    
    y_off = 138 
    for tx in reversed(recent_tx):
        try:
            amt_str = str(tx.get('Amount', '0'))
            val = float(re.sub(r'[^\d.-]', '', amt_str))
            t_type = str(tx.get('Type', ''))
            is_neg = val < 0 or '-' in t_type or '-' in amt_str
            
            # --- PIXEL PERFECT BRACKETS & SYMBOLS ---
            # Draw '['
            draw.line([COL_BRACKET, y_off, COL_BRACKET+2, y_off], fill=0, width=1)      # Top
            draw.line([COL_BRACKET, y_off, COL_BRACKET, y_off+12], fill=0, width=1)    # Left
            draw.line([COL_BRACKET, y_off+12, COL_BRACKET+2, y_off+12], fill=0, width=1)# Bottom
            
            # Draw ']'
            r_edge = COL_BRACKET + 20
            draw.line([r_edge-2, y_off, r_edge, y_off], fill=0, width=1)      # Top
            draw.line([r_edge, y_off, r_edge, y_off+12], fill=0, width=1)    # Right
            draw.line([r_edge-2, y_off+12, r_edge, y_off+12], fill=0, width=1)# Bottom

            # Draw Minus/Plus (Manual 1px width for sharpness)
            mid_x = COL_BRACKET + 10
            mid_y = y_off + 6
            draw.line([mid_x-4, mid_y, mid_x+4, mid_y], fill=0, width=1) # Horizontal
            if not is_neg:
                draw.line([mid_x, mid_y-4, mid_x, mid_y+4], fill=0, width=1) # Vertical

            # --- ROW TEXT ---
            draw.text((COL_TIME, y_off), format_time(abs(val)), fill=0, font=f_row_time)
            draw.text((COL_DESC, y_off + 2), f"• {str(tx.get('Description', ''))[:11]}", fill=0, font=f_row_desc)
            
            draw.line([10, y_off + 17, 166, y_off + 17], fill=0, width=1)
            y_off += 21 
        except: continue

    # 5. FOOTER
    draw.rectangle([0, 252, 176, 264], fill=255)
    now = datetime.now().strftime("%y-%m-%d %H:%M")
    draw.text((88, 258), f"SYNC: {now}", fill=0, font=f_sync, anchor="mm")

    filename = f"{name.lower()}_pro.bmp"
    img.save(filename)
    return filename

# --- Streamlit Tabs (Kayden / Ethan) ---
# (Keep your existing tab/button logic here)

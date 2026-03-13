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

def format_time(val):
    """Converts a float (1.5) to a string (1h 30m)"""
    try:
        # Absolute value used for the string; the +/- sign is handled separately in the UI
        total_minutes = int(abs(float(val)) * 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes:02d}m"
        return f"{minutes}m"
    except:
        return "0m"

def generate_time_bmp(worksheet, name):
    # --- ROTATED CANVAS (176x264) ---
    width, height = 176, 264
    img = Image.new('1', (width, height), 255) 
    draw = ImageDraw.Draw(img)
    
    font_path = "Roboto-VariableFont_wdth,wght.ttf"
    try:
        font_header = ImageFont.truetype(font_path, 18)
        font_time_val = ImageFont.truetype(font_path, 44)
        font_unit = ImageFont.truetype(font_path, 14)
        font_log_header = ImageFont.truetype(font_path, 16)
        font_symbol = ImageFont.truetype(font_path, 20) # Bold +/- indicators
        font_row_val = ImageFont.truetype(font_path, 15)   # Larger row text
        font_desc = ImageFont.truetype(font_path, 13)
    except:
        st.error("Font error. Check .ttf file.")
        return None

    # --- Data Fetching ---
    try:
        raw_val = worksheet.acell('F1').value
        time_display = format_time(re.sub(r'[^\d.]', '', str(raw_val)))
        
        all_data = worksheet.get_all_records()
        # With Goal removed, we can easily fit the last 4 or 5 logs
        recent_tx = all_data[-5:] 
    except:
        time_display, recent_tx = "0m", []

    # --- UI DRAWING (VERTICAL) ---

    # 1. HEADER BAR
    draw.rectangle([0, 0, 176, 30], fill=0)
    draw.text((88, 15), f"{name.upper()}'S TIME", fill=1, font=font_header, anchor="mm")

    # 2. MAIN TIME DISPLAY
    draw.text((88, 75), time_display, fill=0, font=font_time_val, anchor="mm")
    draw.text((88, 108), "TIME REMAINING", fill=0, font=font_unit, anchor="mm")

    # 3. ACTIVITY HISTORY (Expanded Space)
    draw.line([10, 130, 166, 130], fill=0, width=2)
    draw.text((15, 145), "Activity History", fill=0, font=font_log_header)
    
    y_off = 175
    for tx in recent_tx:
        raw_amt = 0
        try:
            raw_amt = float(re.sub(r'[^\d.-]', '', str(tx.get('Amount', '0'))))
        except: pass
        
        # Large Indicator (+ for Earned, - for Used)
        symbol = "+" if raw_amt >= 0 else "-"
        t_amt_formatted = format_time(raw_amt)
        t_desc = str(tx.get('Description', ''))[:12]
        
        # Draw Symbol (Large and clear)
        draw.text((15, y_off), symbol, fill=0, font=font_symbol, anchor="lm")
        
        # Draw Amount
        draw.text((35, y_off), t_amt_formatted, fill=0, font=font_row_val, anchor="lm")
        
        # Draw Description
        draw.text((95, y_off), f"• {t_desc}", fill=0, font=font_desc, anchor="lm")
        
        y_off += 28 # Bigger gap between rows

    # Final visual touch: Bottom border
    draw.line([0, 263, 176, 263], fill=0, width=1)

    filename = f"{name.lower()}_time.bmp"
    img.save(filename)
    return filename

# --- TABS ---
tab_k, tab_e = st.tabs(["Kayden", "Ethan"])

with tab_k:
    if st.button('🔄 Sync Kayden'):
        ws = sh.worksheet("Kayden")
        fname = generate_time_bmp(ws, "Kayden")
        if fname:
            st.image(fname, width=176)
            with open(fname, "rb") as f:
                st.download_button("📥 Download Kayden BMP", f, file_name=fname)

with tab_e:
    if st.button('🔄 Sync Ethan'):
        ws = sh.worksheet("Ethan")
        fname = generate_time_bmp(ws, "Ethan")
        if fname:
            st.image(fname, width=176)
            with open(fname, "rb") as f:
                st.download_button("📥 Download Ethan BMP", f, file_name=fname)

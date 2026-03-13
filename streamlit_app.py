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
        total_minutes = int(float(val) * 60)
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
        font_time_val = ImageFont.truetype(font_path, 38)
        font_unit = ImageFont.truetype(font_path, 14)
        font_log_header = ImageFont.truetype(font_path, 16)
        font_indicator = ImageFont.truetype(font_path, 18) # Larger for [+] and [-]
        font_row_val = ImageFont.truetype(font_path, 14)   # Increased for readability
        font_row_desc = ImageFont.truetype(font_path, 11)
        font_footer = ImageFont.truetype(font_path, 10)
    except:
        st.error("Font error. Check .ttf file.")
        return None

    # --- Data Fetching ---
    try:
        raw_val = worksheet.acell('F1').value
        time_display = format_time(re.sub(r'[^\d.]', '', str(raw_val)))
        
        all_data = worksheet.get_all_records()
        # Show last 5 logs since goal is gone
        recent_tx = all_data[-5:] 
    except:
        time_display, recent_tx = "0m", []

    # --- UI DRAWING (VERTICAL) ---

    # 1. HEADER BAR
    draw.rectangle([0, 0, 176, 28], fill=0)
    draw.text((88, 14), f"{name.upper()}'S TIME", fill=1, font=font_header, anchor="mm")

    # 2. MAIN TIME DISPLAY
    draw.text((88, 65), time_display, fill=0, font=font_time_val, anchor="mm")
    draw.text((88, 95), "TIME REMAINING", fill=0, font=font_unit, anchor="mm")

    # 3. ACTIVITY LOG SECTION
    draw.line([10, 110, 166, 110], fill=0, width=2)
    draw.text((88, 125), "ACTIVITY HISTORY", fill=0, font=font_log_header, anchor="mm")
    
    y_off = 145
    for tx in reversed(recent_tx): # Show newest at top
        try:
            raw_amt = float(re.sub(r'[^\d.]', '', str(tx.get('Amount', '0'))))
            t_type = str(tx.get('Type', '+'))
            
            # Determine Indicator and formatting
            if '-' in t_type or raw_amt < 0:
                indicator = "[-]"
                formatted_amt = format_time(abs(raw_amt))
            else:
                indicator = "[+]"
                formatted_amt = format_time(raw_amt)

            t_desc = str(tx.get('Description', ''))[:14]
            
            # Draw Larger Indicator
            draw.text((10, y_off), indicator, fill=0, font=font_indicator)
            
            # Draw Amount and Description
            draw.text((45, y_off + 2), formatted_amt, fill=0, font=font_row_val)
            draw.text((100, y_off + 4), f"• {t_desc}", fill=0, font=font_row_desc)
            
            y_off += 22 # More space between rows
        except:
            continue

    # 4. FOOTER (Last Updated)
    draw.line([10, 250, 166, 250], fill=0, width=1)
    now = datetime.now().strftime("%m/%d %H:%M")
    draw.text((88, 258), f"Synced: {now}", fill=0, font=font_footer, anchor="mm")

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

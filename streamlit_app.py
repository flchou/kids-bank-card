import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image, ImageDraw, ImageFont
import re
from datetime import datetime

# --- Auth & Config ---
st.set_page_config(page_title="Time Pass Pro", page_icon="🎫")
st.title("🎫 Time Pass Pro")

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
        if hours > 0:
            return f"{hours}h {minutes:02d}m"
        return f"{minutes}m"
    except: return "0m"

def generate_pro_bmp(worksheet, name):
    width, height = 176, 264
    img = Image.new('1', (width, height), 255) 
    draw = ImageDraw.Draw(img)
    font_path = "Roboto-VariableFont_wdth,wght.ttf"

    try:
        f_name = ImageFont.truetype(font_path, 18)
        f_balance = ImageFont.truetype(font_path, 38)
        f_label = ImageFont.truetype(font_path, 11)
        f_section = ImageFont.truetype(font_path, 13)
        f_row_time = ImageFont.truetype(font_path, 13) # Slightly smaller for alignment
        f_row_desc = ImageFont.truetype(font_path, 10) # Smaller to prevent overflow
        f_sync = ImageFont.truetype(font_path, 9)
    except: return None

    raw_val = worksheet.acell('F1').value
    clean_val = re.sub(r'[^\d.]', '', str(raw_val))
    time_display = format_time(clean_val)
    all_data = worksheet.get_all_records()
    recent_tx = all_data[-5:] 

    # 1. HEADER
    draw.rectangle([0, 0, 176, 30], fill=0)
    draw.text((88, 15), f"{name.upper()} PASS", fill=1, font=f_name, anchor="mm")

    # 2. BALANCE BOX
    draw.rectangle([10, 38, 166, 100], outline=0, width=2)
    draw.text((88, 62), time_display, fill=0, font=f_balance, anchor="mm")
    draw.text((88, 88), "REMAINING BALANCE", fill=0, font=f_label, anchor="mm")

    # 3. SECTION HEADER
    draw.rectangle([10, 110, 166, 127], fill=0)
    draw.text((88, 118), "RECENT ACTIVITY", fill=1, font=f_section, anchor="mm")

# 4. ALIGNED ACTIVITY LOGS
    COL_IND = 10   # Starting X for the symbol
    COL_TIME = 38  # Time 1h 30m
    COL_DESC = 92  # Description
    
    y_off = 138 
    for tx in reversed(recent_tx):
        try:
            amt_str = str(tx.get('Amount', '0'))
            val = float(re.sub(r'[^\d.-]', '', amt_str))
            t_type = str(tx.get('Type', ''))
            
            is_neg = val < 0 or '-' in t_type or '-' in amt_str
            formatted_amt = format_time(abs(val))
            t_desc = str(tx.get('Description', ''))[:12]

            # --- CUSTOM DRAWN INDICATORS ---
            symbol_center_y = y_off + 8 # Adjust to align with text center
            symbol_width = 10           # Length of the minus/plus bars
            
            if is_neg:
                # Long Minus Sign: [ — ]
                # Draw brackets first
                draw.text((COL_IND, y_off), "[   ]", fill=0, font=f_row_time)
                # Draw the long line inside the brackets
                draw.line([COL_IND + 6, symbol_center_y, COL_IND + 6 + symbol_width, symbol_center_y], fill=0, width=2)
            else:
                # Custom Plus Sign: [ + ]
                draw.text((COL_IND, y_off), "[   ]", fill=0, font=f_row_time)
                # Horizontal bar
                draw.line([COL_IND + 6, symbol_center_y, COL_IND + 6 + symbol_width, symbol_center_y], fill=0, width=2)
                # Vertical bar
                draw.line([COL_IND + 6 + (symbol_width//2), symbol_center_y - 5, COL_IND + 6 + (symbol_width//2), symbol_center_y + 5], fill=0, width=2)

            # --- TEXT COLUMNS ---
            draw.text((COL_TIME, y_off), formatted_amt, fill=0, font=f_row_time)
            draw.text((COL_DESC, y_off + 2), f"• {t_desc}", fill=0, font=f_row_desc)
            
            draw.line([10, y_off + 17, 166, y_off + 17], fill=0, width=1)
            y_off += 21 
        except: continue

    # 5. FOOTER (Guaranteed no overlap)
    # Pushed to absolute bottom
    draw.rectangle([0, 252, 176, 264], fill=255) # Clear white safety box
    now = datetime.now().strftime("%Y-%m-%d  %H:%M")
    draw.text((88, 258), f"LATEST SYNC: {now}", fill=0, font=f_sync, anchor="mm")

    filename = f"{name.lower()}_pro.bmp"
    img.save(filename)
    return filename

# --- Streamlit Tabs ---
tab_k, tab_e = st.tabs(["Kayden", "Ethan"])

with tab_k:
    if st.button('🔄 Update Kayden Pass'):
        ws = sh.worksheet("Kayden")
        fname = generate_pro_bmp(ws, "Kayden")
        if fname:
            st.image(fname, width=176)
            with open(fname, "rb") as f:
                st.download_button("📥 Download Kayden BMP", f, file_name=fname)

with tab_e:
    if st.button('🔄 Update Ethan Pass'):
        ws = sh.worksheet("Ethan")
        fname = generate_pro_bmp(ws, "Ethan")
        if fname:
            st.image(fname, width=176)
            with open(fname, "rb") as f:
                st.download_button("📥 Download Ethan BMP", f, file_name=fname)

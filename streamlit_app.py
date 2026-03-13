import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image, ImageDraw, ImageFont
import re
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="Time Pass Pro", page_icon="🎫")
st.title("🎫 Time Pass Professional")

# --- Auth (Assuming secrets are set) ---
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
    # 176x264 Native Resolution
    width, height = 176, 264
    img = Image.new('1', (width, height), 255) 
    draw = ImageDraw.Draw(img)
    font_path = "Roboto-VariableFont_wdth,wght.ttf"

    try:
        # Load various sizes for hierarchy
        f_name = ImageFont.truetype(font_path, 18)    # Bold-ish name
        f_balance = ImageFont.truetype(font_path, 40) # Large Hero Balance
        f_label = ImageFont.truetype(font_path, 11)   # Small labels
        f_section = ImageFont.truetype(font_path, 13) # Section headers
        f_row_time = ImageFont.truetype(font_path, 14) # Row values
        f_row_desc = ImageFont.truetype(font_path, 11) # Row descriptions
        f_sync = ImageFont.truetype(font_path, 9)     # Tiny footer
    except: return None

    # --- Data Processing ---
    raw_val = worksheet.acell('F1').value
    clean_val = re.sub(r'[^\d.]', '', str(raw_val))
    time_display = format_time(clean_val)
    all_data = worksheet.get_all_records()
    recent_tx = all_data[-5:] 

    # --- UI LAYOUT ---

    # 1. THE TOP "IDENTITY" BLOCK
    draw.rectangle([0, 0, 176, 30], fill=0) # Black Header
    draw.text((88, 15), f"{name.upper()} PASS", fill=1, font=f_name, anchor="mm")

    # 2. THE HERO BALANCE BLOCK
    # A subtle box to frame the time
    draw.rectangle([10, 40, 166, 105], outline=0, width=2)
    draw.text((88, 68), time_display, fill=0, font=f_balance, anchor="mm")
    draw.text((88, 92), "REMAINING BALANCE", fill=0, font=f_label, anchor="mm")

    # 3. ACTIVITY SECTION HEADER
    # Uses a "pill" style label
    draw.rectangle([10, 115, 166, 132], fill=0)
    draw.text((88, 123), "RECENT ACTIVITY", fill=1, font=f_section, anchor="mm")

    # 4. POLISHED LOGS
    y_off = 145
    for tx in reversed(recent_tx):
        try:
            amt_str = str(tx.get('Amount', '0'))
            val = float(re.sub(r'[^\d.-]', '', amt_str))
            t_type = str(tx.get('Type', ''))
            
            # Logic for [+] or [-]
            is_neg = val < 0 or '-' in t_type or '-' in amt_str
            indicator = "[-]" if is_neg else "[+]"
            formatted_amt = format_time(abs(val))
            t_desc = str(tx.get('Description', ''))[:14]

            # Column 1: Indicator
            draw.text((12, y_off), indicator, fill=0, font=f_row_time)
            # Column 2: Time Value
            draw.text((42, y_off), formatted_amt, fill=0, font=f_row_time)
            # Column 3: Description (Grayer/Thinner feel)
            draw.text((100, y_off + 2), f"• {t_desc}", fill=0, font=f_row_desc)
            
            # Sub-divider line (Dotted style simulation)
            draw.line([12, y_off + 18, 164, y_off + 18], fill=0, width=1)
            y_off += 23
        except: continue

    # 5. FOOTER
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
                st.download_button("📥 Download Pro BMP", f, file_name=fname)

with tab_e:
    if st.button('🔄 Update Ethan Pass'):
        ws = sh.worksheet("Ethan")
        fname = generate_pro_bmp(ws, "Ethan")
        if fname:
            st.image(fname, width=176)
            with open(fname, "rb") as f:
                st.download_button("📥 Download Pro BMP", f, file_name=fname)

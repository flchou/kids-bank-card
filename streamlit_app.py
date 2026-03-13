import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image, ImageDraw, ImageFont
import re
from datetime import datetime

# --- 1. Page Config & Setup ---
st.set_page_config(page_title="Time Pass Pro", page_icon="🎫")
st.title("🎫 Time Pass Pro")

# --- 2. Google Sheets Authentication ---
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

try:
    # Ensure 'gcp_service_account' is set in your Streamlit Cloud Secrets
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)
    
    # Updated to your specific sheet URL
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1IiFdAUJrcKRuxREGMkn7ejWv395UZJtVIoekk8bVx50/edit"
    sh = gc.open_by_url(SHEET_URL)
except Exception as e:
    st.error(f"Authentication or Sheet Error: {e}")
    st.stop()

# --- 3. Helper Functions ---
def format_time(val):
    """Converts a float/string (1.5) to a formatted string (1h 30m)"""
    try:
        total_minutes = int(float(val) * 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes:02d}m"
        return f"{minutes}m"
    except:
        return "0m"

def generate_pro_bmp(worksheet, name):
    # Native Resolution: 176w x 264h (Vertical)
    width, height = 176, 264
    img = Image.new('1', (width, height), 255) 
    draw = ImageDraw.Draw(img)
    
    # Ensure this .ttf file is in the same folder as your script in GitHub
    font_path = "Roboto-VariableFont_wdth,wght.ttf"
    try:
        f_name = ImageFont.truetype(font_path, 18)
        f_balance = ImageFont.truetype(font_path, 36)
        f_label = ImageFont.truetype(font_path, 11)
        f_section = ImageFont.truetype(font_path, 13)
        f_row_time = ImageFont.truetype(font_path, 12)
        f_row_desc = ImageFont.truetype(font_path, 10)
        f_sync = ImageFont.truetype(font_path, 9)
    except Exception as e:
        st.error(f"Font Loading Error: {e}")
        return None

    # Data Fetching
    try:
        raw_val = worksheet.acell('F1').value
        clean_val = re.sub(r'[^\d.]', '', str(raw_val))
        time_display = format_time(clean_val)
        
        all_data = worksheet.get_all_records()
        recent_tx = all_data[-5:] 
    except Exception as e:
        st.error(f"Data Fetching Error for {name}: {e}")
        return None

    # --- UI DRAWING ---
    # 1. Header
    draw.rectangle([0, 0, 176, 30], fill=0)
    draw.text((88, 15), f"{name.upper()} PASS", fill=1, font=f_name, anchor="mm")

    # 2. Balance Box
    draw.rectangle([10, 38, 166, 100], outline=0, width=1)
    draw.text((88, 62), time_display, fill=0, font=f_balance, anchor="mm")
    draw.text((88, 88), "REMAINING BALANCE", fill=0, font=f_label, anchor="mm")

    # 3. Section Header
    draw.rectangle([10, 110, 166, 127], fill=0)
    draw.text((88, 118), "RECENT ACTIVITY", fill=1, font=f_section, anchor="mm")

    # 4. Activity Logs
    col_bracket = 8
    col_time = 38
    col_desc = 92
    y_off = 138 

    for tx in reversed(recent_tx):
        try:
            amt_str = str(tx.get('Amount', '0'))
            # Keep negative sign for detection
            clean_amt = re.sub(r'[^\d.-]', '', amt_str)
            val = float(clean_amt)
            
            t_type = str(tx.get('Type', ''))
            is_neg = val < 0 or '-' in t_type or '-' in amt_str
            
            # --- Manual Brackets ---
            # '['
            draw.line([col_bracket, y_off, col_bracket+2, y_off], fill=0, width=1)
            draw.line([col_bracket, y_off, col_bracket, y_off+12], fill=0, width=1)
            draw.line([col_bracket, y_off+12, col_bracket+2, y_off+12], fill=0, width=1)
            # ']'
            r_e = col_bracket + 20
            draw.line([r_e-2, y_off, r_e, y_off], fill=0, width=1)
            draw.line([r_e, y_off, r_e, y_off+12], fill=0, width=1)
            draw.line([r_e-2, y_off+12, r_e, y_off+12], fill=0, width=1)

            # --- Symbol ---
            mid_x, mid_y = col_bracket + 10, y_off + 6
            draw.line([mid_x-4, mid_y, mid_x+4, mid_y], fill=0, width=1)
            if not is_neg:
                draw.line([mid_x, mid_y-4, mid_x, mid_y+4], fill=0, width=1)

            # --- Text ---
            draw.text((col_time, y_off), format_time(abs(val)), fill=0, font=f_row_time)
            desc = str(tx.get('Description', ''))[:11]
            draw.text((col_desc, y_off + 2), f"• {desc}", fill=0, font=f_row_desc)
            
            draw.line([10, y_off + 17, 166, y_off + 17], fill=0, width=1)
            y_off += 21 
        except:
            continue

    # 5. Footer
    draw.rectangle([0, 252, 176, 264], fill=255)
    now = datetime.now().strftime("%y-%m-%d %H:%M")
    draw.text((88, 258), f"SYNC: {now}", fill=0, font=f_sync, anchor="mm")

    filename = f"{name.lower()}_card.bmp"
    img.save(filename)
    return filename

# --- 4. Streamlit UI Logic ---
tab_k, tab_e = st.tabs(["Kayden", "Ethan"])

with tab_k:
    if st.button('🔄 Sync Kayden'):
        with st.spinner('Updating Kayden...'):
            ws_k = sh.worksheet("Kayden")
            fname_k = generate_pro_bmp(ws_k, "Kayden")
            if fname_k:
                st.image(fname_k, width=176)
                with open(fname_k, "rb") as f:
                    st.download_button("📥 Download Kayden BMP", f, file_name=fname_k)

with tab_e:
    if st.button('🔄 Sync Ethan'):
        with st.spinner('Updating Ethan...'):
            ws_e = sh.worksheet("Ethan")
            fname_e = generate_pro_bmp(ws_e, "Ethan")
            if fname_e:
                st.image(fname_e, width=176)
                with open(fname_e, "rb") as f:
                    st.download_button("📥 Download Ethan BMP", f, file_name=fname_e)

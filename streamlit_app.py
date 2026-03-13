import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image, ImageDraw, ImageFont
import re
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Kids Bank Sync", page_icon="📟")
st.title("📟 Kids Bank Card Sync")

# 2. Google Sheets Authentication
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)
    # Using your specific Sheet URL
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1IiFdAUJrcKRuxREGMkn7ejWv395UZJtVIoekk8bVx50/edit"
    sh = gc.open_by_url(SHEET_URL)
except Exception as e:
    st.error(f"Authentication Error: {e}")
    st.stop()

def generate_bmp(worksheet, name):
    # --- NATIVE SPEC CANVAS (264x176) ---
    width, height = 264, 176
    img = Image.new('1', (width, height), 255) 
    draw = ImageDraw.Draw(img)
    
    font_path = "Roboto-VariableFont_wdth,wght.ttf"
    try:
        font_header = ImageFont.truetype(font_path, 14)
        font_time = ImageFont.truetype(font_path, 10)
        font_balance = ImageFont.truetype(font_path, 38)
        font_sub = ImageFont.truetype(font_path, 11)
        font_act_hd = ImageFont.truetype(font_path, 12)
        font_row = ImageFont.truetype(font_path, 11)
        font_goal = ImageFont.truetype(font_path, 10)
    except:
        st.error(f"Font error for {name}. Check if .ttf is in repo.")
        return None

    # --- Data Fetching ---
    try:
        raw_bal = worksheet.acell('F1').value
        total_balance = float(re.sub(r'[^\d.]', '', raw_bal))
        
        goal_name = worksheet.acell('H1').value or "Savings"
        
        raw_target = worksheet.acell('I1').value
        goal_target = float(re.sub(r'[^\d.]', '', raw_target)) if raw_target else 100.0
        
        all_data = worksheet.get_all_records()
        recent_tx = all_data[-2:] # Last 2 rows
    except Exception as e:
        st.error(f"Error fetching data for {name}: {e}")
        return None

    # --- UI DRAWING ---

    # 1. HEADER
    draw.rectangle([0, 0, 264, 20], fill=0)
    draw.text((8, 10), f"{name.upper()}'S CARD", fill=1, font=font_header, anchor="lm")
    draw.text((256, 10), datetime.now().strftime("%H:%M"), fill=1, font=font_time, anchor="rm")

    # 2. BALANCE
    draw.text((132, 55), f"${total_balance:.2f}", fill=0, font=font_balance, anchor="mm")
    draw.text((132, 82), "TOTAL AVAILABLE", fill=0, font=font_sub, anchor="mm")

    # 3. RECENT ACTIVITY
    draw.line([15, 95, 249, 95], fill=0, width=1)
    draw.text((15, 105), "Recent Activity", fill=0, font=font_act_hd)
    
    y_off = 122
    for tx in recent_tx:
        t_amt = f"{tx.get('Type', '+')}${tx.get('Amount', '0')}"
        t_desc = str(tx.get('Description', ''))[:15]
        draw.text((15, y_off), t_amt, fill=0, font=font_row)
        draw.text((70, y_off), f"• {t_desc}", fill=0, font=font_row)
        y_off += 15

    # 4. GOAL FOOTER
    draw.line([15, 152, 249, 152], fill=0, width=1)
    progress_pct = min(total_balance / goal_target, 1.0) if goal_target > 0 else 0
    draw.text((15, 164), goal_name, fill=0, font=font_goal, anchor="lm")
    
    # Progress Bar with Safety Check
    bar_coords = [80, 160, 180, 168]
    draw.rectangle(bar_coords, outline=0, width=1)
    fill_width = int(100 * progress_pct)
    if fill_width > 4: # Prevents the negative-width ValueError
        draw.rectangle([bar_coords[0]+2, bar_coords[1]+2, bar_coords[0]+fill_width-2, bar_coords[3]-2], fill=0)
        
    draw.text((249, 164), f"{int(progress_pct*100)}%", fill=0, font=font_goal, anchor="rm")

    filename = f"{name.lower()}_card.bmp"
    img.save(filename)
    return filename

# --- STREAMLIT TABS ---
tab_k, tab_e = st.tabs(["Kayden's Account", "Ethan's Account"])

with tab_k:
    if st.button('🔄 Sync Kayden'):
        ws = sh.worksheet("Kayden")
        fname = generate_bmp(ws, "Kayden")
        if fname:
            st.image(fname, width=264)
            with open(fname, "rb") as f:
                st.download_button("📥 Download Kayden.bmp", f, file_name=fname)

with tab_e:
    if st.button('🔄 Sync Ethan'):
        ws = sh.worksheet("Ethan")
        fname = generate_bmp(ws, "Ethan")
        if fname:
            st.image(fname, width=264)
            with open(fname, "rb") as f:
                st.download_button("📥 Download Ethan.bmp", f, file_name=fname)

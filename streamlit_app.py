import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image, ImageDraw, ImageFont
import re
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="E-Paper Sync", page_icon="📟")
st.title("📟 E-Paper Card Sync (264x176)")

# 2. Google Sheets Authentication
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1IiFdAUJrcKRuxREGMkn7ejWv395UZJtVIoekk8bVx50/edit"
    sh = gc.open_by_url(SHEET_URL)
    worksheet = sh.sheet1
except Exception as e:
    st.error(f"Authentication Error: {e}")
    st.stop()

def generate_bmp():
    # --- NATIVE SPEC CANVAS (264x176) ---
    width, height = 264, 176
    img = Image.new('1', (width, height), 255) 
    draw = ImageDraw.Draw(img)
    
    # --- PIXEL-SENSITIVE FONT LOADING ---
    font_path = "Roboto-VariableFont_wdth,wght.ttf"
    try:
        # Sizes are dramatically reduced for the 176px height
        font_header = ImageFont.truetype(font_path, 14)
        font_time = ImageFont.truetype(font_path, 10)
        font_balance = ImageFont.truetype(font_path, 38)
        font_sub = ImageFont.truetype(font_path, 11)
        font_act_hd = ImageFont.truetype(font_path, 12)
        font_row = ImageFont.truetype(font_path, 11)
        font_goal = ImageFont.truetype(font_path, 10)
    except:
        st.error("Font file error.")
        return None

    # --- Data Fetching ---
    try:
        raw_bal = worksheet.acell('F1').value
        total_balance = float(re.sub(r'[^\d.]', '', raw_bal))
        goal_name = worksheet.acell('H1').value or "Goal"
        raw_target = worksheet.acell('I1').value
        goal_target = float(re.sub(r'[^\d.]', '', raw_target)) if raw_target else 100.0
        
        all_data = worksheet.get_all_records()
        recent_tx = all_data[-2:] # Only 2 rows to fit 176px height clearly
    except:
        total_balance, goal_name, goal_target, recent_tx = 0.0, "Error", 100.0, []

    # --- UI DRAWING (PIXEL PERFECT) ---

    # 1. HEADER (Slim 20px bar)
    draw.rectangle([0, 0, 264, 20], fill=0)
    draw.text((8, 10), "LEO'S BANK", fill=1, font=font_header, anchor="lm")
    now = datetime.now().strftime("%H:%M")
    draw.text((256, 10), now, fill=1, font=font_time, anchor="rm")

    # 2. BALANCE SECTION (Centered in top half)
    draw.text((132, 55), f"${total_balance:.2f}", fill=0, font=font_balance, anchor="mm")
    draw.text((132, 82), "TOTAL AVAILABLE", fill=0, font=font_sub, anchor="mm")
    
    # Tiny Plus Icon
    draw.ellipse([215, 35, 235, 55], outline=0, width=1)
    draw.line([220, 45, 230, 45], fill=0, width=1)
    draw.line([225, 40, 225, 50], fill=0, width=1)

    # 3. RECENT ACTIVITY (Middle)
    draw.line([15, 95, 249, 95], fill=0, width=1)
    draw.text((15, 105), "Recent Activity", fill=0, font=font_act_hd)
    
    y_off = 122
    for tx in recent_tx:
        t_amt = f"{tx.get('Type', '+')}${tx.get('Amount', '0')}"
        t_desc = str(tx.get('Description', ''))[:15] # Shorten desc to fit
        
        draw.text((15, y_off), t_amt, fill=0, font=font_row)
        draw.text((70, y_off), f"• {t_desc}", fill=0, font=font_row)
        y_off += 15

    # 4. SAVINGS GOAL (Footer)
    draw.line([15, 152, 249, 152], fill=0, width=1)
    
    progress_pct = min(total_balance / goal_target, 1.0) if goal_target > 0 else 0
    draw.text((15, 164), goal_name, fill=0, font=font_goal, anchor="lm")
    
    # Small Progress Bar
    bar_coords = [80, 160, 180, 168]
    draw.rectangle(bar_coords, outline=0, width=1)
    fill_width = int(100 * progress_pct)
    if fill_width > 0:
        draw.rectangle([bar_coords[0]+2, bar_coords[1]+2, bar_coords[0]+fill_width-2, bar_coords[3]-2], fill=0)
        
    draw.text((249, 164), f"{int(progress_pct*100)}%", fill=0, font=font_goal, anchor="rm")

    # --- SAVE ---
    img.save("transfer.bmp")
    return img

if st.button('🔄 Sync & Generate (264x176)'):
    with st.spinner('Optimizing for e-paper...'):
        generated_img = generate_bmp()
        if generated_img:
            # Show the image small in Streamlit so user sees the real scale
            st.image(generated_img, caption="1:1 E-Paper Preview", width=264)
            with open("transfer.bmp", "rb") as file:
                st.download_button(label="📥 Download BMP", data=file, file_name="transfer.bmp", mime="image/bmp")

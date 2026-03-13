import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image, ImageDraw, ImageFont
import re
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Kids Bank Card Sync", page_icon="💰")
st.title("💰 Kids Bank Card Sync")

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
    # --- Canvas Setup (800x480) ---
    width, height = 800, 480
    img = Image.new('1', (width, height), 255) 
    draw = ImageDraw.Draw(img)
    
    # --- Font Loading ---
    font_path = "Roboto-VariableFont_wdth,wght.ttf"
    try:
        font_header = ImageFont.truetype(font_path, 26)     # Shrank from 32
        font_timestamp = ImageFont.truetype(font_path, 18)  # Shrank from 20
        font_balance = ImageFont.truetype(font_path, 90)    # Shrank by ~80% of original
        font_sub = ImageFont.truetype(font_path, 24)        # Shrank from 30
        font_activity_hd = ImageFont.truetype(font_path, 24)
        font_date = ImageFont.truetype(font_path, 20)
        font_activity = ImageFont.truetype(font_path, 24)
        font_goal = ImageFont.truetype(font_path, 22)
    except:
        st.error("Font file error. Ensure it's in your GitHub repo.")
        return None

    # --- Data Fetching ---
    try:
        raw_bal = worksheet.acell('F1').value
        total_balance = float(re.sub(r'[^\d.]', '', raw_bal))
        goal_name = worksheet.acell('H1').value or "Savings"
        raw_target = worksheet.acell('I1').value
        goal_target = float(re.sub(r'[^\d.]', '', raw_target)) if raw_target else 100.0
        
        all_data = worksheet.get_all_records()
        recent_tx = all_data[-3:] if len(all_data) >= 3 else all_data
    except Exception as e:
        total_balance, goal_name, goal_target, recent_tx = 0.0, "Error", 100.0, []

    # --- UI DRAWING ---

    # 1. HEADER (Reduced Size)
    draw.rectangle([0, 0, 800, 50], fill=0) # Height reduced to 50
    draw.text((40, 25), "MY HOME BANK • LEO'S CARD", fill=1, font=font_header, anchor="lm")
    now = datetime.now().strftime("%b %d, %H:%M")
    draw.text((760, 25), f"Updated: {now}", fill=1, font=font_timestamp, anchor="rm")

    # 2. BALANCE SECTION (Tighter spacing)
    draw.text((400, 135), f"${total_balance:.2f}", fill=0, font=font_balance, anchor="mm")
    draw.text((400, 200), "TOTAL AVAILABLE", fill=0, font=font_sub, anchor="mm")
    
    # Plus Icon (Slightly smaller and moved up)
    draw.ellipse([640, 90, 710, 160], outline=0, width=3)
    draw.line([655, 125, 695, 125], fill=0, width=4) # Horizontal
    draw.line([675, 105, 675, 145], fill=0, width=4) # Vertical

    # 3. RECENT ACTIVITY
    draw.line([50, 230, 750, 230], fill=0, width=2) # Main Divider moved up
    draw.text((60, 250), "Recent Activity", fill=0, font=font_activity_hd)
    
    y_off = 290 # Start higher
    for tx in recent_tx:
        t_date = str(tx.get('Date', ''))[:10] 
        t_type = tx.get('Type', '+')
        t_amt = tx.get('Amount', '0')
        t_desc = tx.get('Description', 'Item')
        
        draw.text((60, y_off), t_date, fill=0, font=font_date)
        draw.text((200, y_off), f"{t_type}${t_amt}", fill=0, font=font_activity)
        draw.text((350, y_off), f"• {t_desc}", fill=0, font=font_activity)
        y_off += 38 # Tighter row spacing

    # 4. SAVINGS GOAL (With new sectional divider)
    draw.line([50, 420, 750, 420], fill=0, width=2) # NEW Sectional Divider
    
    progress_pct = min(total_balance / goal_target, 1.0) if goal_target > 0 else 0
    draw.text((60, 450), f"Saving for: {goal_name}", fill=0, font=font_goal, anchor="lm")
    draw.text((740, 450), f"{int(progress_pct*100)}% of ${goal_target:.0f}", fill=0, font=font_goal, anchor="rm")
    
    # Progress Bar Pill (Centered at bottom)
    bar_coords = [250, 442, 550, 458]
    draw.rectangle(bar_coords, outline=0, width=2)
    fill_end = bar_coords[0] + (300 * progress_pct)
    if progress_pct > 0.02:
        draw.rectangle([bar_coords[0]+3, bar_coords[1]+3, fill_end-3, bar_coords[3]-3], fill=0)

    # --- SAVE ---
    img.save("transfer.bmp")
    return img

if st.button('🔄 Sync Data & Generate Card'):
    with st.spinner('Accessing the vault...'):
        generated_img = generate_bmp()
        if generated_img:
            st.image(generated_img, caption="New Card Preview", use_container_width=True)
            with open("transfer.bmp", "rb") as file:
                st.download_button(label="📥 Download BMP", data=file, file_name="transfer.bmp", mime="image/bmp")

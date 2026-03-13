import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image, ImageDraw, ImageFont
import re
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Kids Bank Card Sync", page_icon="💰")
st.title("💰 Kids Bank Card Sync")
st.markdown("Update your Google Sheet, then click the button below to generate the new card image.")

# 2. Google Sheets Authentication
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)

    # Spreadsheet URL
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1IiFdAUJrcKRuxREGMkn7ejWv395UZJtVIoekk8bVx50/edit"
    sh = gc.open_by_url(SHEET_URL)
    worksheet = sh.sheet1
except Exception as e:
    st.error(f"Authentication Error: {e}")
    st.stop()

def generate_bmp():
    # --- Canvas Setup (High Res 800x480) ---
    width, height = 800, 480
    img = Image.new('1', (width, height), 255) 
    draw = ImageDraw.Draw(img)
    
    # --- Font Loading ---
    font_path = "Roboto-VariableFont_wdth,wght.ttf"
    try:
        font_header = ImageFont.truetype(font_path, 32)
        font_timestamp = ImageFont.truetype(font_path, 20)
        font_balance = ImageFont.truetype(font_path, 110) # Slightly smaller to prevent edge-clashing
        font_sub = ImageFont.truetype(font_path, 28)
        font_activity_hd = ImageFont.truetype(font_path, 24)
        font_date = ImageFont.truetype(font_path, 22)
        font_activity = ImageFont.truetype(font_path, 26)
        font_goal = ImageFont.truetype(font_path, 24)
    except:
        st.error("Font file error. Ensure it's in your GitHub repo.")
        return None

    # --- Data Fetching (Including New Goal Cells) ---
    try:
        # F1 = Total Balance
        raw_bal = worksheet.acell('F1').value
        total_balance = float(re.sub(r'[^\d.]', '', raw_bal))
        
        # H1 = Goal Name (e.g., "New Bike")
        goal_name = worksheet.acell('H1').value or "Savings Goal"
        
        # I1 = Goal Target Value (e.g., "100")
        raw_target = worksheet.acell('I1').value
        goal_target = float(re.sub(r'[^\d.]', '', raw_target)) if raw_target else 100.0
        
        all_data = worksheet.get_all_records()
        recent_tx = all_data[-3:] if len(all_data) >= 3 else all_data
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        total_balance, goal_name, goal_target, recent_tx = 0.0, "Error", 100.0, []

    # --- UI DRAWING ---

    # 1. HEADER
    draw.rectangle([0, 0, 800, 70], fill=0)
    draw.text((40, 35), "MY HOME BANK • LEO'S CARD", fill=1, font=font_header, anchor="lm")
    now = datetime.now().strftime("%b %d, %H:%M")
    draw.text((760, 35), f"Updated: {now}", fill=1, font=font_timestamp, anchor="rm")

    # 2. BALANCE SECTION
    draw.text((400, 160), f"${total_balance:.2f}", fill=0, font=font_balance, anchor="mm")
    draw.text((400, 235), "TOTAL AVAILABLE", fill=0, font=font_sub, anchor="mm")
    
    # Plus Icon Circle
    draw.ellipse([630, 110, 710, 190], outline=0, width=4)
    draw.line([645, 150, 695, 150], fill=0, width=5) # Horizontal
    draw.line([670, 125, 670, 175], fill=0, width=5) # Vertical

    # 3. RECENT ACTIVITY
    draw.line([50, 275, 750, 275], fill=0, width=2)
    draw.text((60, 295), "Recent Activity", fill=0, font=font_activity_hd)
    
    y_off = 335 
    for tx in recent_tx:
        t_date = str(tx.get('Date', ''))[:10] 
        t_type = tx.get('Type', '+')
        t_amt = tx.get('Amount', '0')
        t_desc = tx.get('Description', 'Item')
        
        draw.text((60, y_off), t_date, fill=0, font=font_date)
        draw.text((220, y_off), f"{t_type}${t_amt}", fill=0, font=font_activity)
        draw.text((380, y_off), f"• {t_desc}", fill=0, font=font_activity)
        y_off += 42 

    # 4. DYNAMIC GOAL SECTION
    progress_pct = min(total_balance / goal_target, 1.0) if goal_target > 0 else 0
    
    draw.text((60, 445), f"Saving for: {goal_name}", fill=0, font=font_goal, anchor="lm")
    draw.text((740, 445), f"{int(progress_pct*100)}% of ${goal_target:.0f}", fill=0, font=font_goal, anchor="rm")
    
    # Progress Bar Pill
    bar_coords = [250, 437, 550, 453]
    draw.rectangle(bar_coords, outline=0, width=2)
    fill_end = bar_coords[0] + (300 * progress_pct)
    if progress_pct > 0.02:
        draw.rectangle([bar_coords[0]+3, bar_coords[1]+3, fill_end-3, bar_coords[3]-3], fill=0)

    # --- SAVE ---
    img.save("transfer.bmp")
    return img

# Streamlit UI Logic
if st.button('🔄 Sync Data & Generate Card'):
    with st.spinner('Accessing the vault...'):
        generated_img = generate_bmp()
        if generated_img:
            st.image(generated_img, caption="New Card Preview", use_container_width=True)
            with open("transfer.bmp", "rb") as file:
                st.download_button(
                    label="📥 Download BMP to Phone",
                    data=file,
                    file_name="transfer.bmp",
                    mime="image/bmp"
                )
            st.success("Card generated! Tap to update.")

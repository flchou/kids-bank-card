import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image, ImageDraw
import re

# 1. Setup Streamlit Page
st.set_page_config(page_title="Kids Bank Card", page_icon="💰")
st.title("💰 Kids Bank Card Generator")

# 2. Connect to Google Sheets using Streamlit Secrets
# (We will set these secrets in Step 3)
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
gc = gspread.authorize(creds)

# Open your sheet
sh = gc.open('docs.google.com/spreadsheets/d/1IiFdAUJrcKRuxREGMkn7ejWv395UZJtVIoekk8bVx50/edit')
worksheet = sh.sheet1

def generate_bmp():
    # Fetch Data
    raw_val = worksheet.acell('F1').value
    clean_val = re.sub(r'[^\d.]', '', raw_val)
    total_balance = float(clean_val)
    
    # Create Image (250x122)
    img = Image.new('1', (250, 122), 255)
    draw = ImageDraw.Draw(img)
    
    # Draw UI (Simplified for Demo)
    draw.rectangle([0, 0, 250, 20], fill=0)
    draw.text((10, 4), "KIDS HOME BANK", fill=1)
    draw.text((10, 30), f"Balance: ${total_balance:.2f}", fill=0)
    
    # Progress Bar
    draw.rectangle([10, 50, 240, 60], outline=0)
    progress = min(total_balance / 100.0, 1.0)
    draw.rectangle([12, 52, 12 + int(226 * progress), 58], fill=0)
    
    img.save("transfer.bmp")
    return img

if st.button('🔄 Sync & Generate New Image'):
    img = generate_bmp()
    st.image(img, caption="Preview for your Card", use_container_width=True)
    
    # Provide download button for the phone
    with open("transfer.bmp", "rb") as file:
        st.download_button(
            label="💾 Download BMP for NFC Tap",
            data=file,
            file_name="transfer.bmp",
            mime="image/bmp"
        )

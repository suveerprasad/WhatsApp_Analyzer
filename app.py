import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import bcrypt
import dataset
import functions
import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from whatsapp_analysis_storage import init_analysis_table, store_analysis_results, get_user_analyses
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# Database connection and initialization
def init_db():
    conn = sqlite3.connect("app_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password TEXT,
            profile_photo_url TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            dataset_name TEXT,
            data TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    return conn

def init_otp_table():
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_otps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            used BOOLEAN DEFAULT 0
        )
    """)
    conn.commit()

def init_email_verification_table():
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_verification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            verified BOOLEAN DEFAULT 0
        )
    """)
    conn.commit()

def send_welcome_email(email, username):
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')

    if not all([smtp_username, smtp_password]):
        print("Error: SMTP credentials not properly configured")
        return False

    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = email
    msg['Subject'] = 'Welcome to WhatsApp Chat Analyzer!'

    body = f"""
    Dear {username},

    Welcome to WhatsApp Chat Analyzer! Your account has been successfully created.

    You can now log in to:
    - Analyze your WhatsApp chats
    - View detailed statistics and visualizations
    - Track conversation patterns
    - And much more!

    Thank you for joining us.

    Best regards,
    WhatsApp Chat Analyzer Team
    """
    
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending welcome email: {str(e)}")
        return False

def send_otp_email(email, otp):
    # Add more detailed error handling and logging
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')

    # Validate required environment variables
    if not all([smtp_username, smtp_password]):
        print("Error: SMTP credentials not properly configured in environment variables")
        return False

    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = email
    msg['Subject'] = 'Password Reset OTP'

    body = f"""
    Your OTP for password reset is: {otp}
    
    This OTP will expire in 10 minutes.
    If you didn't request this password reset, please ignore this email.
    """
    
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Create SMTP connection with timeout
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        
        # Identify ourselves to SMTP server
        server.ehlo()
        
        # Enable TLS encryption
        server.starttls()
        
        # Re-identify ourselves over TLS connection
        server.ehlo()
        
        # Login to server
        server.login(smtp_username, smtp_password)
        
        # Send email
        server.send_message(msg)
        
        # Close connection
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("SMTP Authentication failed. Please check your username and password.")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP error occurred: {str(e)}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return False

def send_verification_email(email, otp):
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')

    if not all([smtp_username, smtp_password]):
        print("Error: SMTP credentials not properly configured")
        return False

    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = email
    msg['Subject'] = 'Email Verification OTP'

    body = f"""
    Thank you for signing up! Your verification OTP is: {otp}
    
    This OTP will expire in 10 minutes.
    If you didn't create an account, please ignore this email.
    """
    
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending verification email: {str(e)}")
        return False

def verify_email_otp(conn, email, otp):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM email_verification 
        WHERE email = ? AND otp = ? AND expires_at > CURRENT_TIMESTAMP 
        AND verified = 0 ORDER BY created_at DESC LIMIT 1
    """, (email, otp))
    result = cursor.fetchone()
    if result:
        cursor.execute("UPDATE email_verification SET verified = 1 WHERE id = ?", (result[0],))
        conn.commit()
        return True
    return False

def store_verification_otp(conn, email, otp):
    cursor = conn.cursor()
    expires_at = datetime.now() + timedelta(minutes=10)
    cursor.execute(
        "INSERT INTO email_verification (email, otp, expires_at) VALUES (?, ?, ?)",
        (email, otp, expires_at)
    )
    conn.commit()

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def store_otp(email, otp):
    cursor = conn.cursor()
    expires_at = datetime.now() + timedelta(minutes=10)
    cursor.execute(
        "INSERT INTO password_reset_otps (email, otp, expires_at) VALUES (?, ?, ?)",
        (email, otp, expires_at)
    )
    conn.commit()

def verify_otp(email, otp):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM password_reset_otps 
        WHERE email = ? AND otp = ? AND expires_at > CURRENT_TIMESTAMP 
        AND used = 0 ORDER BY created_at DESC LIMIT 1
    """, (email, otp))
    result = cursor.fetchone()
    if result:
        # Mark OTP as used
        cursor.execute("UPDATE password_reset_otps SET used = 1 WHERE id = ?", (result[0],))
        conn.commit()
        return True
    return False

def forgot_password_page():
    st.title("Forgot Password")
    
    if "reset_stage" not in st.session_state:
        st.session_state.reset_stage = "email"
    
    if st.session_state.reset_stage == "email":
        with st.form("forgot_password_form"):
            email = st.text_input("Enter your email address")
            submitted = st.form_submit_button("Send OTP")
            
            if submitted and email:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                user = cursor.fetchone()
                if user:
                    otp = generate_otp()
                    if send_otp_email(email, otp):
                        store_otp(email, otp)
                        st.session_state.reset_email = email
                        st.session_state.reset_stage = "otp"
                        st.success("OTP sent to your email!")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to send OTP email. Please try again.")
                else:
                    st.error("No account found with this email address.")
    
    elif st.session_state.reset_stage == "otp":
        with st.form("verify_otp_form"):
            otp = st.text_input("Enter OTP from your email")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            submitted = st.form_submit_button("Reset Password")
            
            if submitted:
                if not otp or not new_password or not confirm_password:
                    st.error("Please fill in all fields.")
                    return
                
                if new_password != confirm_password:
                    st.error("Passwords don't match.")
                    return
                
                if len(new_password) < 6:
                    st.error("Password must be at least 6 characters long.")
                    return
                
                if verify_otp(st.session_state.reset_email, otp):
                    cursor = conn.cursor()
                    hashed_password = hash_password(new_password)
                    cursor.execute(
                        "UPDATE users SET password = ? WHERE email = ?",
                        (hashed_password, st.session_state.reset_email)
                    )
                    conn.commit()
                    
                    st.success("Password reset successful! Please login with your new password.")
                    st.session_state.reset_stage = "email"
                    del st.session_state.reset_email
                    st.session_state.page = "Login"
                    st.experimental_rerun()
                else:
                    st.error("Invalid or expired OTP. Please try again.")

        if st.button("Back"):
            st.session_state.reset_stage = "email"
            if "reset_email" in st.session_state:
                del st.session_state.reset_email
            st.experimental_rerun()

# Initialize database connection
conn = init_db()
init_analysis_table(conn)
init_otp_table()
init_email_verification_table()


# User authentication functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(hashed, password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def login(username, password):
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM users WHERE username = ? OR email = ?", (username, username))
    user = cursor.fetchone()
    if user and check_password(user[1], password):
        return user[0]
    return None

def signup(username, email, password, profile_photo=None):
    try:
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        
        # Upload profile photo to Cloudinary if provided
        profile_photo_url = None
        if profile_photo:
            upload_result = cloudinary.uploader.upload(profile_photo)
            profile_photo_url = upload_result['secure_url']
        
        cursor.execute(
            "INSERT INTO users (username, email, password, profile_photo_url) VALUES (?, ?, ?, ?)",
            (username, email, hashed_password, profile_photo_url)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None

def get_user_profile(user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT username, email, profile_photo_url FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()

def update_profile(user_id, username=None, email=None, password=None, profile_photo=None):
    try:
        cursor = conn.cursor()
        updates = []
        values = []
        
        if username:
            updates.append("username = ?")
            values.append(username)
        
        if email:
            updates.append("email = ?")
            values.append(email)
        
        if password:
            updates.append("password = ?")
            values.append(hash_password(password))
        
        if profile_photo:
            upload_result = cloudinary.uploader.upload(profile_photo)
            updates.append("profile_photo_url = ?")
            values.append(upload_result['secure_url'])
        
        if updates:
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            values.append(user_id)
            cursor.execute(query, tuple(values))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False
    return False

def clear_whatsapp_visualization_history():
    cursor = conn.cursor()
    cursor.execute("DELETE FROM whatsapp_analyses WHERE user_id = ?", (st.session_state["user_id"],))
    conn.commit()
    st.success("WhatsApp visualization history cleared successfully.")

# Page functions
def main_page():
    st.title('WhatsApp Chat Analyzer')
    st.markdown('Developed using Streamlit, SQLite, and Python, incorporating libraries such as Pandas, Plotly, and Matplotlib for data processing, visualization, and interactivity.')
    st.caption(
        'This application lets you analyze Whatsapp conversations in a very comprehensive manner, with charts, metrics, '
        'and other forms of analysis.')

    with st.expander('See!!.. How it works?'):
        st.subheader('Steps to Analyze:')
        st.markdown(
            '1. Export the chat by going to WhatsApp on your phone, opening the chat, clicking on the three dots, '
            'selecting "More," and then choosing "Export Chat" without media. Save the file to your desired location.')
        st.markdown(
            '2. Browse or drag and drop the chat file.')
        st.markdown('3. Select a user or group to analyze, or leave the default setting of "All" to analyze for all users.')
        st.markdown('4. Click the "Show Analysis" button.')
        st.markdown(
            '5. Enable "Wide mode" for a better viewing experience in settings, or close the sidebar on mobile for improved'
            ' view.')
        st.markdown(
            '6. To analyze for a single user, select their name from the dropdown and click "Show Analysis" again.')
        st.markdown(
            '7. Repeat the steps for additional chats.')
    st.sidebar.success("Select a page above.")

def login_page():
    if "user_id" in st.session_state:
        st.warning("You are already logged in!")
        return
    
    st.title("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if username and password:
                user_id = login(username, password)
                if user_id:
                    st.session_state["user_id"] = user_id
                    st.session_state["page"] = "Dashboard"
                    st.experimental_rerun()
                else:
                    st.error("Invalid credentials")
            else:
                st.error("Please fill in all fields")
    
    # Add this after the form
    if st.button("Forgot Password?"):
        st.session_state["page"] = "Forgot Password"
        st.experimental_rerun()

# def signup_page():
#     if "user_id" in st.session_state:
#         st.warning("You have logged in already!")
#         return
    
#     st.title("Sign Up")
#     with st.form("signup_form"):
#         username = st.text_input("Username")
#         email = st.text_input("Email")
#         password = st.text_input("Password", type="password")
#         profile_photo = st.file_uploader("Profile Photo", type=['jpg', 'jpeg', 'png'])
#         submitted = st.form_submit_button("Sign Up")
        
#         if submitted:
#             if len(username) < 3:
#                 st.error("Username must be at least 3 characters long")
#                 return
#             if len(password) < 6:
#                 st.error("Password must be at least 6 characters long")
#                 return
#             if not email or '@' not in email:
#                 st.error("Please enter a valid email address")
#                 return
                
#             user_id = signup(username, email, password, profile_photo)
#             if user_id:
#                 st.success("Sign up successful! Please login.")
#                 st.session_state["page"] = "Login"
#                 st.experimental_rerun()
#             else:
#                 st.error("Username or email already exists")

def signup_page():
    if "user_id" in st.session_state:
        st.warning("You are already logged in!")
        return
    
    st.title("Sign Up")
    
    if "signup_stage" not in st.session_state:
        st.session_state.signup_stage = "details"
    
    if st.session_state.signup_stage == "details":
        with st.form("signup_details_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            profile_photo = st.file_uploader("Profile Photo", type=['jpg', 'jpeg', 'png'])
            submitted = st.form_submit_button("Continue")
            
            if submitted:
                if len(username) < 3:
                    st.error("Username must be at least 3 characters long")
                    return
                if len(password) < 6:
                    st.error("Password must be at least 6 characters long")
                    return
                if not email or '@' not in email:
                    st.error("Please enter a valid email address")
                    return
                
                # Check if username or email already exists
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
                if cursor.fetchone():
                    st.error("Username or email already exists")
                    return
                
                # Store signup details in session state
                st.session_state.signup_username = username
                st.session_state.signup_email = email
                st.session_state.signup_password = password
                st.session_state.signup_profile_photo = profile_photo
                
                # Generate and send OTP
                otp = generate_otp()
                if send_verification_email(email, otp):
                    store_verification_otp(conn, email, otp)  # Pass conn here
                    st.session_state.signup_stage = "verification"
                    st.success("Verification code sent to your email!")
                    st.experimental_rerun()
                else:
                    st.error("Failed to send verification email. Please try again.")
    
    elif st.session_state.signup_stage == "verification":
        with st.form("signup_verification_form"):
            st.write(f"Please enter the verification code sent to {st.session_state.signup_email}")
            otp = st.text_input("Verification Code")
            submitted = st.form_submit_button("Verify and Sign Up")
            
            if submitted:
                if verify_email_otp(conn, st.session_state.signup_email, otp):  # Pass conn here
                    # Create user account
                    user_id = signup(
                        st.session_state.signup_username,
                        st.session_state.signup_email,
                        st.session_state.signup_password,
                        st.session_state.signup_profile_photo
                    )
                    
                    if user_id:
                        # Clear signup session state
                        if send_welcome_email(st.session_state.signup_email, st.session_state.signup_username):
                            st.success("Account created successfully! Welcome email has been sent.")
                        else:
                            st.warning("Account created successfully, but failed to send welcome email.")
                        for key in ['signup_stage', 'signup_username', 'signup_email', 
                                  'signup_password', 'signup_profile_photo']:
                            if key in st.session_state:
                                del st.session_state[key]
                        
                        st.success("Sign up successful! Please login.")
                        st.session_state["page"] = "Login"
                        st.experimental_rerun()
                    else:
                        st.error("Failed to create account. Please try again.")
                else:
                    st.error("Invalid or expired verification code.")
        
        if st.button("Back"):
            st.session_state.signup_stage = "details"
            st.experimental_rerun()

def profile_settings_page():
    if "user_id" not in st.session_state:
        st.warning("Please log in first.")
        st.session_state["page"] = "Login"
        st.experimental_rerun()
        return
    
    st.title("Profile Settings")
    
    # Get current profile information
    current_profile = get_user_profile(st.session_state["user_id"])
    if not current_profile:
        st.error("Could not load profile information")
        return
    
    current_username, current_email, current_photo = current_profile
    
    # Display current profile photo
    if current_photo:
        st.image(current_photo, width=200, caption="Current Profile Photo")
    
    with st.form("profile_settings_form"):
        st.subheader("Update Profile Information")
        
        new_username = st.text_input("New Username", value=current_username)
        new_email = st.text_input("New Email", value=current_email)
        new_password = st.text_input("New Password (leave blank to keep current)", type="password")
        new_profile_photo = st.file_uploader("New Profile Photo", type=['jpg', 'jpeg', 'png'])
        
        submitted = st.form_submit_button("Update Profile")
        
        if submitted:
            # Validate inputs
            if new_username and len(new_username) < 3:
                st.error("Username must be at least 3 characters long")
                return
            if new_password and len(new_password) < 6:
                st.error("Password must be at least 6 characters long")
                return
            if new_email and '@' not in new_email:
                st.error("Please enter a valid email address")
                return
            
            # Update profile
            success = update_profile(
                st.session_state["user_id"],
                username=new_username if new_username != current_username else None,
                email=new_email if new_email != current_email else None,
                password=new_password if new_password else None,
                profile_photo=new_profile_photo
            )
            
            if success:
                st.success("Profile updated successfully!")
                st.experimental_rerun()
            else:
                st.error("Failed to update profile. Username or email might already be in use.")

def dashboard_page():
    if "user_id" not in st.session_state:
        st.warning("Please log in first.")
        st.session_state["page"] = "Login"
        st.experimental_rerun()
        return
    
    cursor = conn.cursor()
    user_profile = get_user_profile(st.session_state["user_id"])

    st.title("Dashboard")
    
    # Display user profile information
    if user_profile:
        col1, col2 = st.columns([1, 3])
        with col1:
            if user_profile[2]:  # profile_photo_url
                st.image(user_profile[2], width=150, caption="Profile Photo")
        with col2:
            st.write(f"Welcome, {user_profile[0]}!")
            st.write(f"Email: {user_profile[1]}")
    
    # Dataset management
    cursor.execute("SELECT id, dataset_name FROM datasets WHERE user_id = ?", (st.session_state["user_id"],))
    datasets = cursor.fetchall()

    if datasets:
        st.subheader("Your Datasets")
        for dataset_id, dataset_name in datasets:
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(f"View {dataset_name}", key=f"view_{dataset_id}"):
                    cursor.execute("SELECT data FROM datasets WHERE id = ?", (dataset_id,))
                    data = cursor.fetchone()[0]
                    df = pd.read_json(data)
                    st.write(df)
            with col2:
                if st.button(f"Delete", key=f"delete_{dataset_id}"):
                    cursor.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
                    conn.commit()
                    st.experimental_rerun()

    st.subheader("Upload New Dataset")
    uploaded_file = st.file_uploader("Upload a CSV or TXT File")
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, on_bad_lines='skip')
            elif uploaded_file.name.endswith('.txt'):
                df = pd.read_csv(uploaded_file, delimiter="\t", on_bad_lines='skip')
            else:
                st.error("Unsupported file format. Please upload a CSV or TXT file.")
                return
            
            st.write("Preview of the data:")
            st.write(df.head())
            
            with st.form("save_dataset"):
                dataset_name = st.text_input("Dataset Name")
                submitted = st.form_submit_button("Save Dataset")
                if submitted:
                    if not dataset_name:
                        st.error("Please provide a dataset name")
                        return
                    data = df.to_json()
                    cursor.execute(
                        "INSERT INTO datasets (user_id, dataset_name, data) VALUES (?, ?, ?)",
                        (st.session_state["user_id"], dataset_name, data)
                    )
                    conn.commit()
                    st.success("Dataset saved successfully")
                    st.experimental_rerun()
        except Exception as e:
            st.error(f"Failed to process the file. Error: {str(e)}")
    
    # WhatsApp Analysis History
    st.subheader("WhatsApp Analysis History")
    if st.button("Clear History"):
        clear_whatsapp_visualization_history()
        st.experimental_rerun()

    cursor.execute("""
        SELECT 
            analysis_date,
            chat_name,
            total_messages,
            total_users,
            total_words,
            total_media,
            total_links,
            most_active_user,
            chat_start_date,
            chat_end_date
        FROM whatsapp_analyses 
        WHERE user_id = ? 
        ORDER BY analysis_date DESC
    """, (st.session_state["user_id"],))
    
    analyses = cursor.fetchall()
    
    if analyses:
        for analysis in analyses:
            with st.expander(f"Analysis from {analysis[0]} - {analysis[1]}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Messages", analysis[2])
                    st.metric("Media Shared", analysis[5])
                
                with col2:
                    st.metric("Users", analysis[3])
                    st.metric("Links Shared", analysis[6])
                
                with col3:
                    st.metric("Words", analysis[4])
                    st.metric("Most Active", analysis[7])
                
                st.caption(f"Chat Period: {analysis[8]} to {analysis[9]}")
    else:
        st.info("No WhatsApp chat analyses yet. Try analyzing a chat in the WhatsApp Analysis section!")

def whatsapp_analysis_page():
    if "user_id" not in st.session_state:
        st.warning("Please log in first.")
        st.session_state["page"] = "Login"
        st.experimental_rerun()
        return
    
    from whatsapp_visualization import run_whatsapp_analysis
    run_whatsapp_analysis()

def logout():
    if "user_id" in st.session_state:
        del st.session_state["user_id"]
        st.session_state["page"] = "Main"
        st.experimental_rerun()

# Page routing
if "page" not in st.session_state:
    st.session_state["page"] = "Main"

# Sidebar navigation
# Sidebar navigation (continued)
st.sidebar.title("Navigation")

# Show different navigation options based on login state
if "user_id" in st.session_state:
    pages = {
        "Dashboard": dashboard_page,
        "WhatsApp Analysis": whatsapp_analysis_page,
        "Profile Settings": profile_settings_page,
    }
    
    # Add logout button at the bottom of sidebar
    st.sidebar.markdown("---")  # Separator line
    if st.sidebar.button("Logout"):
        logout()
else:
    pages = {
        "Main": main_page,
        "Login": login_page,
        "Sign Up": signup_page,
        "Forgot Password": forgot_password_page
    }

# Navigation buttons
for page_name in pages:
    if st.sidebar.button(page_name):
        st.session_state["page"] = page_name
        st.experimental_rerun()

# Display current page
if st.session_state["page"] in pages:
    pages[st.session_state["page"]]()
else:
    st.session_state["page"] = "Main"
    main_page()

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("WhatsApp Chat Analyzer © 2024")

# Handle session expiry
if "user_id" in st.session_state:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (st.session_state["user_id"],))
    if not cursor.fetchone():
        del st.session_state["user_id"]
        st.session_state["page"] = "Login"
        st.experimental_rerun()
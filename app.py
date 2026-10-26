import streamlit as st
import pandas as pd
import numpy as np
import os
import hashlib
from datetime import datetime
from github import Github

# ==========================================
# 0. 基本設定與密碼雜湊
# ==========================================
USER_DB_FILE = "users_db.csv"
PROFILE_DB_FILE = "user_profiles.csv"
DATA_FILE = "workout_data.csv"
REPORT_FILE = "workout_reports.csv"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================
# 1. GitHub 自動同步核心引擎 (防雲端洗機)
# ==========================================
def sync_to_github(file_path, df):
    """儲存本地 CSV 並自動同步上 GitHub Repo 防洗機"""
    csv_content = df.to_csv(index=False, encoding='utf-8-sig')
    with open(file_path, "w", encoding='utf-8-sig') as f:
        f.write(csv_content)
        
    # 如果有設定 GitHub Secrets 就自動推上雲端
    if "GITHUB_TOKEN" in st.secrets and "GITHUB_REPO" in st.secrets:
        try:
            g = Github(st.secrets["GITHUB_TOKEN"])
            repo = g.get_repo(st.secrets["GITHUB_REPO"])
            try:
                contents = repo.get_contents(file_path)
                repo.update_file(contents.path, f"Auto-update {file_path}", csv_content, contents.sha)
            except:
                repo.create_file(file_path, f"Auto-create {file_path}", csv_content)
        except Exception as e:
            st.toast(f"⚠️ 雲端同步提示: {e}")

# ==========================================
# 2. 資料讀寫與驗證函數
# ==========================================
def load_users():
    if os.path.exists(USER_DB_FILE):
        try:
            return pd.read_csv(USER_DB_FILE)
        except:
            pass
    default_users = pd.DataFrame([
        {"username": "admin", "password": hash_password("123456"), "name": "系統管理員"},
        {"username": "coach", "password": hash_password("coach888"), "name": "專業教練"}
    ])
    sync_to_github(USER_DB_FILE, default_users)
    return default_users

def save_users(users_df):
    sync_to_github(USER_DB_FILE, users_df)

def load_profiles():
    if os.path.exists(PROFILE_DB_FILE):
        try:
            return pd.read_csv(PROFILE_DB_FILE)
        except:
            pass
    return pd.DataFrame(columns=["username", "height", "initial_weight", "target_weight", "age", "gender", "setup_complete"])

def save_profiles(profiles_df):
    sync_to_github(PROFILE_DB_FILE, profiles_df)

def validate_and_fix_df(df):
    expected_cols = ["username", "date", "exercise", "weight", "reps", "sets"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""
    return df

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            return pd.read_csv(DATA_FILE)
        except:
            pass
    return pd.DataFrame(columns=["username", "date", "exercise", "weight", "reps", "sets"])

def save_data(df):
    safe_df = validate_and_fix_df(df)
    sync_to_github(DATA_FILE, safe_df)

def load_reports():
    if os.path.exists(REPORT_FILE):
        try:
            return pd.read_csv(REPORT_FILE)
        except:
            pass
    return pd.DataFrame(columns=["username", "date", "report"])

def save_reports(df):
    sync_to_github(REPORT_FILE, df)

# ==========================================
# 3. Streamlit 介面與業務邏輯
# ==========================================
st.set_page_config(page_title="健身追蹤系統", page_icon="💪", layout="wide")

st.title("💪 個人化健身追蹤與管理系統")

# 初始化 Session State 登入狀態
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

users_df = load_users()
profiles_df = load_profiles()
workout_df = load_data()
reports_df = load_reports()

# 未登入：顯示登入/註冊頁面
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔐 登入系統", "📝 註冊帳號"])
    
    with tab1:
        st.subheader("請登入")
        login_user = st.text_input("使用者名稱 (Username)", key="login_username")
        login_pass = st.text_input("密碼 (Password)", type="password", key="login_password")
        
        if st.button("登入"):
            hashed_p = hash_password(login_pass)
            user_match = users_df[(users_df["username"] == login_user) & (users_df["password"] == hashed_p)]
            if not user_match.empty:
                st.session_state.logged_in = True
                st.session_state.username = login_user
                st.success("登入成功！")
                st.rerun()
            else:
                st.error("使用者名稱或密碼錯誤。")
                
    with tab2:
        st.subheader("新用戶註冊")
        reg_user = st.text_input("設定使用者名稱", key="reg_username")
        reg_name = st.text_input("顯示名稱", key="reg_name")
        reg_pass = st.text_input("設定密碼", type="password", key="reg_password")
        
        if st.button("註冊"):
            if reg_user and reg_pass:
                if reg_user in users_df["username"].values:
                    st.warning("該使用者名稱已被註冊。")
                else:
                    new_user_row = pd.DataFrame([{
                        "username": reg_user,
                        "password": hash_password(reg_pass),
                        "name": reg_name if reg_name else reg_user
                    }])
                    users_df = pd.concat([users_df, new_user_row], ignore_index=True)
                    save_users(users_df)
                    st.success("註冊成功！請切換至登入頁面登入。")
            else:
                st.warning("請填寫完整資訊。")

else:
    # 已登入：主畫面 / Dashboard
    current_user = st.session_state.username
    st.sidebar.success(q_user := f"歡迎返嚟，{current_user}！")
    
    if st.sidebar.button("登出"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
        
    st.sidebar.markdown("---")
    menu = st.sidebar.radio("導覽選單", ["📊 數據儀表板", "🏋️ 記錄訓練", "👤 個人檔案設定"])
    
    # 檢查該用戶是否有填寫 Profile
    user_profile = profiles_df[profiles_df["username"] == current_user]
    
    if menu == "👤 個人檔案設定" or user_profile.empty or not user_profile.iloc[0].get("setup_complete", False):
        st.header("👤 個人基本檔案設定")
        st.info("請先完善你的身高、體重等基本數據以獲得準確追蹤。")
        
        # 預填現有資料（如果有的話）
        existing_height = float(user_profile.iloc[0]["height"]) if not user_profile.empty and pd.notna(user_profile.iloc[0]["height"]) else 170.0
        existing_init_w = float(user_profile.iloc[0]["initial_weight"]) if not user_profile.empty and pd.notna(user_profile.iloc[0]["initial_weight"]) else 70.0
        existing_target_w = float(user_profile.iloc[0]["target_weight"]) if not user_profile.empty and pd.notna(user_profile.iloc[0]["target_weight"]) else 65.0
        existing_age = int(user_profile.iloc[0]["age"]) if not user_profile.empty and pd.notna(user_profile.iloc[0]["age"]) else 30
        
        with st.form("profile_form"):
            h = st.number_input("身高 (cm)", value=existing_height)
            iw = st.number_input("初始體重 (kg)", value=existing_init_w)
            tw = st.number_input("目標體重 (kg)", value=existing_target_w)
            age = st.number_input("年齡", value=existing_age)
            gender = st.selectbox("性別", ["男", "Male", "女", "Female"], index=0)
            
            submitted = st.form_submit_button("儲存檔案")
            if submitted:
                new_prof = {
                    "username": current_user,
                    "height": h,
                    "initial_weight": iw,
                    "target_weight": tw,
                    "age": age,
                    "gender": gender,
                    "setup_complete": True
                }
                if not user_profile.empty:
                    profiles_df.loc[profiles_df["username"] == current_user] = pd.DataFrame([new_prof])
                else:
                    profiles_df = pd.concat([profiles_df, pd.DataFrame([new_prof])], ignore_index=True)
                
                save_profiles(profiles_df)
                st.success("個人檔案儲存成功！")
                st.rerun()
                
    elif menu == "📊 數據儀表板":
        st.header("📊 訓練進度儀表板")
        user_data = workout_df[workout_df["username"] == current_user]
        
        if user_data.empty:
            st.info("暫時未有訓練記錄，請前往「記錄訓練」新增數據！")
        else:
            st.dataframe(user_data, use_container_width=True)
            # 可在此處加圖表展示
            st.line_chart(user_data, x="date", y="weight")
            
    elif menu == "🏋️ 記錄訓練":
        st.header("🏋️ 新增今日訓練記錄")
        
        with st.form("workout_form"):
            w_date = st.date_input("訓練日期", value=datetime.today())
            exercise = st.text_input("訓練動作 (例如: 槓鈴深蹲、臥推)")
            weight = st.number_input("使用重量 (kg)", min_value=0.0, step=0.5)
            reps = st.number_input("每組次數 (Reps)", min_value=1, step=1)
            sets = st.number_input("組數 (Sets)", min_value=1, step=1)
            
            w_submitted = st.form_submit_button("儲存訓練記錄")
            if w_submitted:
                new_row = pd.DataFrame([{
                    "username": current_user,
                    "date": str(w_date),
                    "exercise": exercise,
                    "weight": weight,
                    "reps": reps,
                    "sets": sets
                }])
                workout_df = pd.concat([workout_df, new_row], ignore_index=True)
                save_data(workout_df)
                st.success("訓練記錄已成功儲存並同步至 GitHub！")
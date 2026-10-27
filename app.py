import streamlit as st
import pandas as pd
import datetime
import os
import hashlib
import io
import re
import plotly.express as px
import plotly.graph_objects as go
from github import Github

# 安全匯入 pypdf
try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

# Set page configuration
st.set_page_config(
    page_title="專業多組重量與有氧訓練追蹤系統",
    page_icon="🏋️‍♂️",
    layout="wide"
)

# 密碼雜湊輔助函式
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 帳號密碼資料庫檔案
USER_DB_FILE = "users_db.csv"
PROFILE_DB_FILE = "user_profiles.csv"

# ----------------- GitHub 自動同步核心引擎 -----------------
def sync_to_github(file_path, df):
    """儲存本地 CSV 並自動同步上 GitHub Repo 防雲端休眠洗機"""
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

# 初始化 Session State
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'name' not in st.session_state:
    st.session_state.name = ""

# ----------------- 登入畫面 (Login Screen) -----------------
if not st.session_state.logged_in:
    st.title("🔐 會員登入系統 - 健身與進度追蹤平台")
    st.markdown("請輸入您的帳號與密碼以登入系統。若無帳號可於下方註冊。")
    
    users_df = load_users()
    
    tab_login, tab_register = st.tabs(["🔑 登入系統", "📝 註冊新帳號"])
    
    with tab_login:
        with st.form("login_form"):
            input_user = st.text_input("帳號 (Username)")
            input_pass = st.text_input("密碼 (Password)", type="password")
            login_btn = st.form_submit_button("登入系統")
            
            if login_btn:
                hashed_input_pass = hash_password(input_pass)
                matched_user = users_df[(users_df["username"] == input_user) & (users_df["password"] == hashed_input_pass)]
                if not matched_user.empty:
                    st.session_state.logged_in = True
                    st.session_state.username = input_user
                    st.session_state.name = matched_user.iloc[0]["name"]
                    st.success(f"歡迎回來，{st.session_state.name}！")
                    st.rerun()
                else:
                    st.error("❌ 帳號或密碼錯誤，請重新輸入。")
                    
    with tab_register:
        with st.form("register_form"):
            new_user = st.text_input("設定新帳號 (Username)")
            new_name = st.text_input("您的姓名或暱稱 (Name)")
            new_pass = st.text_input("設定密碼 (Password)", type="password")
            new_pass_confirm = st.text_input("確認密碼 (Confirm Password)", type="password")
            register_btn = st.form_submit_button("註冊帳號")
            
            if register_btn:
                if not new_user or not new_pass or not new_name:
                    st.warning("⚠️ 請完整填寫所有欄位。")
                elif new_pass != new_pass_confirm:
                    st.error("❌ 兩次輸入的密碼不一致。")
                elif new_user in users_df["username"].values:
                    st.error("❌ 此帳號已經存在，請更換帳號名稱。")
                else:
                    new_row = pd.DataFrame([{"username": new_user, "password": hash_password(new_pass), "name": new_name}])
                    users_df = pd.concat([users_df, new_row], ignore_index=True)
                    save_users(users_df)
                    
                    profiles_df = load_profiles()
                    if new_user not in profiles_df["username"].values:
                        empty_profile = pd.DataFrame([{
                            "username": new_user, "height": 0.0, "initial_weight": 0.0, 
                            "target_weight": 0.0, "age": 25, "gender": "不透露", "setup_complete": False
                        }])
                        profiles_df = pd.concat([profiles_df, empty_profile], ignore_index=True)
                        save_profiles(profiles_df)
                        
                    st.success("✅ 註冊成功！請切換至「登入系統」分頁進行登入。")

# ----------------- 登入後畫面 -----------------
else:
    profiles_df = load_profiles()
    user_prof = profiles_df[profiles_df["username"] == st.session_state.username]
    
    is_setup_complete = False
    if not user_prof.empty:
        is_setup_complete = bool(user_prof.iloc[0]["setup_complete"])

    if st.session_state.username == "admin":
        is_setup_complete = True

    if not is_setup_complete:
        st.title(f"👋 歡迎加入，{st.session_state.name}！")
        st.markdown("### 📋 首次登入設定：請填寫您的基本身體密碼以解鎖專屬健身分析")
        
        with st.form("first_time_setup_form"):
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                set_height = st.number_input("身高 (cm)", min_value=100.0, max_value=250.0, value=170.0, step=0.5)
                set_init_weight = st.number_input("目前體重 (kg)", min_value=30.0, max_value=250.0, value=70.0, step=0.1)
            with col_s2:
                set_target_weight = st.number_input("目標體重 (kg)", min_value=30.0, max_value=250.0, value=65.0, step=0.1)
                set_age = st.number_input("年齡 (Age)", min_value=10, max_value=100, value=25, step=1)
                
            set_gender = st.selectbox("性別 (Gender)", ["男性", "女性", "其他 / 不透露"])
            setup_submit = st.form_submit_button("🚀 儲存並開始我的健身之旅")
            
            if setup_submit:
                if user_prof.empty:
                    new_p = pd.DataFrame([{
                        "username": st.session_state.username, "height": float(set_height), 
                        "initial_weight": float(set_init_weight), "target_weight": float(set_target_weight), 
                        "age": int(set_age), "gender": str(set_gender), "setup_complete": True
                    }])
                    profiles_df = pd.concat([profiles_df, new_p], ignore_index=True)
                else:
                    mask = profiles_df["username"] == st.session_state.username
                    profiles_df.loc[mask, "height"] = float(set_height)
                    profiles_df.loc[mask, "initial_weight"] = float(set_init_weight)
                    profiles_df.loc[mask, "target_weight"] = float(set_target_weight)
                    profiles_df.loc[mask, "age"] = int(set_age)
                    profiles_df.loc[mask, "gender"] = str(set_gender)
                    profiles_df.loc[mask, "setup_complete"] = True
                
                save_profiles(profiles_df)
                st.success("✅ 個人檔案設定完成！")
                st.rerun()
                
    else:
        top_col1, top_col2 = st.columns([6, 1])
        with top_col1:
            st.title(f"🏋️‍♂️ 健身紀錄與進度追蹤平台 (歡迎, {st.session_state.name}!)")
        with top_col2:
            if st.button("🚪 登出系統"):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.session_state.name = ""
                st.rerun()

        st.markdown("---")

        if st.session_state.username != "admin":
            user_prof = profiles_df[profiles_df["username"] == st.session_state.username]
            cur_prof = user_prof.iloc[0]
            st.sidebar.markdown("### 👤 會員檔案卡片")
            st.sidebar.info(
                f"**姓名**: {st.session_state.name}\n\n"
                f"**身高**: {cur_prof['height']} cm\n\n"
                f"**目標體重**: {cur_prof['target_weight']} kg"
            )
        else:
            st.sidebar.markdown("### 🛡️ 管理員專屬面板")
            st.sidebar.success("您目前以【系統管理員】身分登入，可於右側分頁管理所有會員資料。")

        DATA_FILE = f"workout_data_{st.session_state.username}.csv"
        REPORT_FILE = f"body_reports_{st.session_state.username}.csv"
        REQUIRED_COLUMNS = ["日期", "肌群分類", "動作名稱", "組別", "重量(kg)", "次數", "體重(kg)", "消耗卡路里", "心情指數"]

        def validate_and_fix_df(df):
            if df is None or df.empty:
                return pd.DataFrame(columns=REQUIRED_COLUMNS)
            for col in REQUIRED_COLUMNS:
                if col not in df.columns:
                    if col in ["重量(kg)", "次數", "消耗卡路里", "體重(kg)"]:
                        df[col] = 0.0 if "kg" in col or col == "體重(kg)" else 0
                    else:
                        df[col] = "未分類" if col == "肌群分類" else ("未知動作" if col == "動作名稱" else ("第一組" if col == "組別" else "普通"))
            if "日期" in df.columns:
                try:
                    df["日期"] = pd.to_datetime(df["日期"]).dt.date
                except:
                    df["日期"] = datetime.date.today()
            return df[REQUIRED_COLUMNS]

        def load_data():
            if os.path.exists(DATA_FILE):
                try:
                    df = pd.read_csv(DATA_FILE)
                    return validate_and_fix_df(df)
                except:
                    pass
            init_w = float(user_prof.iloc[0]['initial_weight']) if (st.session_state.username != "admin" and not user_prof.empty) else 70.0
            default_df = pd.DataFrame([
                {
                    "日期": datetime.date(2026, 10, 10),
                    "肌群分類": "胸部 (Chest)",
                    "動作名稱": "槓鈴平地臥推 (Barbell Bench Press)",
                    "組別": "第一組 (Set 1)",
                    "重量(kg)": 50.0,
                    "次數": 12,
                    "體重(kg)": init_w,
                    "消耗卡路里": 180,
                    "心情指數": "開心"
                }
            ])
            return validate_and_fix_df(default_df)

        def save_data(df):
            safe_df = validate_and_fix_df(df)
            sync_to_github(DATA_FILE, safe_df)

        def load_reports():
            if os.path.exists(REPORT_FILE):
                try:
                    return pd.read_csv(REPORT_FILE)
                except:
                    pass
            return pd.DataFrame(columns=["測量日期", "體重(kg)", "骨骼肌重(kg)", "體脂肪率(%)", "健康分數", "AI評語"])

        def save_reports(df):
            sync_to_github(REPORT_FILE, df)

        if 'workout_sets_data' not in st.session_state:
            st.session_state.workout_sets_data = load_data()
        if 'body_reports_data' not in st.session_state:
            st.session_state.body_reports_data = load_reports()

        EXERCISE_DICT = {
            "胸部 (Chest)": [
                "槓鈴平地臥推 (Barbell Bench Press)", "啞鈴平地臥推 (Dumbbell Bench Press)",
                "上斜槓鈴臥推 (Incline Barbell Bench Press)", "上斜啞鈴臥推 (Incline Dumbbell Bench Press)",
                "下斜臥推 (Decline Bench Press)", "胸推機 (Chest Press Machine)",
                "夾胸機 / 蝴蝶機 (Chest Fly / Pec Deck)", "Cable 繩索夾胸 (Cable Crossover)",
                "伏地挺身 (Push-ups)", "雙槓臂屈伸 (Chest Dips)"
            ],
            "背部 (Back)": [
                "傳統硬舉 (Conventional Deadlift)", "相撲硬舉 (Sumo Deadlift)",
                "引體向上 (Pull-ups)", "高位下拉 (Lat Pulldown)",
                "槓鈴俯身划船 (Barbell Row)", "單臂啞鈴划船 (Dumbbell Row)",
                "T-Bar 划船 (T-Bar Row)", "坐姿滑輪划船 (Seated Cable Row)",
                "直臂下壓 (Straight Arm Pulldown)", "反向飛鳥 / 划船 (Rear Delt Fly)"
            ],
            "腿部 (Legs)": [
                "槓鈴深蹲 (Barbell Squat)", "前蹲舉 (Front Squat)",
                "保加利亞分腿蹲 (Bulgarian Split Squat)", "腿部推舉機 (Leg Press)",
                "羅馬尼亞硬舉 (Romanian Deadlift)", "箱式深蹲 (Box Squat)",
                "腿屈伸機 (Leg Extension)", "俯臥腿彎舉 (Leg Curl)",
                "坐姿提踵 (Seated Calf Raise)", "站姿提踵 (Standing Calf Raise)", "臀橋 / 臀推 (Hip Thrust)"
            ],
            "肩膀 (Shoulders)": [
                "站姿槓鈴肩推 (Overhead Press)", "坐姿啞鈴肩推 (Dumbbell Shoulder Press)",
                "啞鈴側平舉 (Lateral Raise)", "Cable 側平舉 (Cable Lateral Raise)",
                "啞鈴前平舉 (Front Raise)", "面拉 (Face Pull)", "阿諾肩推 (Arnold Press)", "直立划船 (Upright Row)"
            ],
            "手臂 (Arms)": [
                "槓鈴二頭彎舉 (Barbell Bicep Curl)", "啞鈴二頭彎舉 (Dumbbell Bicep Curl)",
                "錘式彎舉 (Hammer Curl)", "牧師凳彎舉 (Preacher Curl)", "Cable 二頭彎舉 (Cable Curl)",
                "三頭下壓 (Triceps Pushdown)", "仰臥三頭臂屈伸 (Skull Crusher)",
                "過頭啞鈴三頭伸展 (Overhead Dumbbell Extension)", "雙槓三頭支撐 (Triceps Dips)"
            ],
            "核心 (Core)": [
                "棒式 / 平板支撐 (Plank)", "側棒式 (Side Plank)", "仰臥起坐 / 捲腹 (Crunch)",
                "懸垂舉腿 (Hanging Leg Raise)", "俄羅斯轉體 (Russian Twist)",
                "健腹輪 (Ab Wheel Rollout)", "仰臥抬腿 (Leg Raises)", "鳥狗式 (Bird-Dog)"
            ]
        }

        if st.session_state.username != "admin":
            uploaded_file = st.sidebar.file_uploader("📥 匯入歷史 CSV 紀錄", type=["csv"])
            if uploaded_file is not None:
                try:
                    imported_df = pd.read_csv(uploaded_file)
                    imported_df = validate_and_fix_df(imported_df)
                    c_up1, c_up2 = st.sidebar.columns(2)
                    if c_up1.button("覆蓋現有資料"):
                        st.session_state.workout_sets_data = imported_df
                        save_data(imported_df)
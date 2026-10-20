import streamlit as st
import pandas as pd
import datetime
import os
import hashlib
import plotly.express as px
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(
    page_title="專業多組重量訓練追蹤系統 (自動卡路里計算版)",
    page_icon="🏋️‍♂️",
    layout="wide"
)

# 密碼雜湊輔助函式
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 帳號密碼資料庫檔案
USER_DB_FILE = "users_db.csv"
PROFILE_DB_FILE = "user_profiles.csv"

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
    default_users.to_csv(USER_DB_FILE, index=False)
    return default_users

def save_users(users_df):
    users_df.to_csv(USER_DB_FILE, index=False)

def load_profiles():
    if os.path.exists(PROFILE_DB_FILE):
        try:
            return pd.read_csv(PROFILE_DB_FILE)
        except:
            pass
    return pd.DataFrame(columns=["username", "height", "initial_weight", "target_weight", "age", "gender", "setup_complete"])

def save_profiles(profiles_df):
    profiles_df.to_csv(PROFILE_DB_FILE, index=False)

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
                        "username": st.session_state.username, "height": set_height, 
                        "initial_weight": set_init_weight, "target_weight": set_target_weight, 
                        "age": set_age, "gender": set_gender, "setup_complete": True
                    }])
                    profiles_df = pd.concat([profiles_df, new_p], ignore_index=True)
                else:
                    profiles_df.loc[profiles_df["username"] == st.session_state.username, ["height", "initial_weight", "target_weight", "age", "gender", "setup_complete"]] = [set_height, set_init_weight, set_target_weight, set_age, set_gender, True]
                
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

        cur_prof = profiles_df[profiles_df["username"] == st.session_state.username].iloc[0]
        st.sidebar.markdown("### 👤 會員檔案卡片")
        st.sidebar.info(
            f"**姓名**: {st.session_state.name}\n\n"
            f"**身高**: {cur_prof['height']} cm\n\n"
            f"**目標體重**: {cur_prof['target_weight']} kg"
        )

        DATA_FILE = f"workout_data_{st.session_state.username}.csv"

        def load_data():
            if os.path.exists(DATA_FILE):
                try:
                    df = pd.read_csv(DATA_FILE)
                    if "日期" in df.columns:
                        df["日期"] = pd.to_datetime(df["日期"]).dt.date
                    return df
                except:
                    pass
            return pd.DataFrame([
                {
                    "日期": datetime.date(2026, 10, 10),
                    "肌群分類": "胸部 (Chest)",
                    "動作名稱": "槓鈴平地臥推 (Barbell Bench Press)",
                    "組別": "第一組 (Set 1)",
                    "重量(kg)": 50.0,
                    "次數": 12,
                    "體重(kg)": float(cur_prof['initial_weight']),
                    "消耗卡路里": 180,
                    "心情指數": "開心"
                }
            ])

        def save_data(df):
            df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

        if 'workout_sets_data' not in st.session_state:
            st.session_state.workout_sets_data = load_data()

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
            ],
            "有氧運動 (Cardio)": [
                "跑步機跑步 (Treadmill Running)", "室內固定式腳踏車 (Stationary Bike)",
                "橢圓機 (Elliptical Trainer)", "划船機 (Rowing Machine)",
                "階梯機 (Stair Climber)", "跳繩 (Jump Rope)", "高強度間歇訓練 HIIT"
            ]
        }

        uploaded_file = st.sidebar.file_uploader("📥 匯入歷史 CSV 紀錄", type=["csv"])
        if uploaded_file is not None:
            try:
                imported_df = pd.read_csv(uploaded_file)
                if "日期" in imported_df.columns:
                    imported_df["日期"] = pd.to_datetime(imported_df["日期"]).dt.date
                
                c_up1, c_up2 = st.sidebar.columns(2)
                if c_up1.button("覆蓋現有資料"):
                    st.session_state.workout_sets_data = imported_df
                    save_data(imported_df)
                    st.sidebar.success("✅ 已覆蓋匯入並存檔！")
                if c_up2.button("合併追加資料"):
                    combined_df = pd.concat([st.session_state.workout_sets_data, imported_df], ignore_index=True).drop_duplicates()
                    st.session_state.workout_sets_data = combined_df
                    save_data(combined_df)
                    st.sidebar.success("✅ 已合併追加並存檔！")
            except Exception as e:
                st.sidebar.error(f"解析失敗: {e}")

        st.sidebar.markdown("---")
        st.sidebar.header("📝 逐組輸入今日訓練紀錄")
        with st.sidebar.form("multiset_form", clear_on_submit=False):
            date_val = st.date_input("日期 Date", datetime.date.today())
            
            muscle_group = st.selectbox("選擇主肌群 Muscle Group", list(EXERCISE_DICT.keys()))
            available_exercises = EXERCISE_DICT[muscle_group]
            exercise_name = st.selectbox("動作名稱 Exercise Name", available_exercises + ["其他自訂 (Other)"])
            
            if exercise_name == "其他自訂 (Other)":
                exercise_name = st.text_input("請輸入自訂動作名稱", "自訂動作")
            
            c_b1, c_b2 = st.columns(2)
            with c_b1:
                body_weight = st.number_input("當日體重 (kg)", min_value=30.0, max_value=250.0, value=float(cur_prof['initial_weight']), step=0.1)
            with c_b2:
                st.markdown("**🔥 卡路里消耗 (Auto)**")
                st.info("系統將根據下方各組重量與次數自動計算！")
                
            mood_val = st.selectbox("心情指數 / 訓練情緒", ["很開心", "開心", "普通", "不開心"])
            
            st.markdown("---")
            st.markdown("### 🔢 各組重量與次數設定 (Set 1 ~ Set 6)")
            
            sets_config = [
                ("第一組 (Set 1)", 50.0, 12),
                ("第二組 (Set 2)", 55.0, 10),
                ("第三組 (Set 3)", 60.0, 8),
                ("第四組 (Set 4)", 60.0, 8),
                ("第五組 (Set 5)", 0.0, 0),
                ("第六組 (Set 6)", 0.0, 0)
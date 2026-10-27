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
                        st.sidebar.success("✅ 已安全覆蓋匯入並同步至 GitHub！")
                    if c_up2.button("合併追加資料"):
                        combined_df = pd.concat([st.session_state.workout_sets_data, imported_df], ignore_index=True).drop_duplicates()
                        combined_df = validate_and_fix_df(combined_df)
                        st.session_state.workout_sets_data = combined_df
                        save_data(combined_df)
                        st.sidebar.success("✅ 已安全合併追加並同步至 GitHub！")
                except Exception as e:
                    st.sidebar.error(f"解析失敗: {e}")

            st.sidebar.markdown("---")
            st.sidebar.header("🏃‍♂️ 記錄有氧運動 (Aerobic Activity)")
            with st.sidebar.form("aerobic_form", clear_on_submit=False):
                aerobic_date = st.date_input("有氧日期 Date", datetime.date.today(), key="ae_date")
                aerobic_type = st.selectbox("有氧項目 Aerobic Type", [
                    "跑步機跑步 (Treadmill Running)", "室內固定式腳踏車 (Stationary Bike)", 
                    "橢圓機 (Elliptical Trainer)", "划船機 (Rowing Machine)", 
                    "階梯機 (Stair Climber)", "戶外跑步 (Outdoor Running)", 
                    "游泳 (Swimming)", "其他有氧 (Other Cardio)"
                ], key="ae_type")
                
                ae_col1, ae_col2 = st.columns(2)
                with ae_col1:
                    duration_min = st.number_input("持續時間 (DURATION 分鐘)", min_value=1, max_value=300, value=30, step=5)
                    distance_km = st.number_input("距離 (DISTANCE 公里)", min_value=0.0, max_value=100.0, value=5.0, step=0.1)
                with ae_col2:
                    speed_resist = st.number_input("速度/阻力 (SPEED/RESIST)", min_value=0.0, max_value=100.0, value=10.0, step=0.5)
                    
                calculated_ae_cals = int(duration_min * 9.5)
                st.info(f"🔥 **自動計算有氧消耗**: ~ {calculated_ae_cals} kcal (依 {duration_min} 分鐘持續時間估算)")
                    
                ae_mood = st.selectbox("心情指數", ["很開心", "開心", "普通", "不開心"], key="ae_mood")
                
                ae_submitted = st.form_submit_button("🏃‍♂️ 儲存有氧運動記錄")
                if ae_submitted:
                    init_w = float(user_prof.iloc[0]['initial_weight']) if not user_prof.empty else 70.0
                    new_ae_row = pd.DataFrame([{
                        "日期": aerobic_date,
                        "肌群分類": "有氧運動 (Cardio)",
                        "動作名稱": aerobic_type,
                        "組別": f"持續 {duration_min}分",
                        "重量(kg)": distance_km,
                        "次數": int(speed_resist * 10),
                        "體重(kg)": init_w,
                        "消耗卡路里": calculated_ae_cals,
                        "心情指數": ae_mood
                    }])
                    updated_df = pd.concat([st.session_state.workout_sets_data, new_ae_row], ignore_index=True)
                    st.session_state.workout_sets_data = validate_and_fix_df(updated_df)
                    save_data(st.session_state.workout_sets_data)
                    st.sidebar.success(f"✅ 成功儲存有氧紀錄並同步至 GitHub！")

            st.sidebar.markdown("---")
            st.sidebar.header("📝 逐組輸入重量訓練紀錄")
            muscle_group = st.sidebar.selectbox("選擇主肌群 Muscle Group", list(EXERCISE_DICT.keys()))
            available_exercises = EXERCISE_DICT[muscle_group]
            exercise_name = st.sidebar.selectbox("動作名稱 Exercise Name", available_exercises + ["其他自訂 (Other)"])
            
            if exercise_name == "其他自訂 (Other)":
                exercise_name = st.sidebar.text_input("請輸入自訂動作名稱", "自訂動作")

            with st.sidebar.form("multiset_form", clear_on_submit=False):
                date_val = st.date_input("日期 Date", datetime.date.today())
                c_b1, c_b2 = st.columns(2)
                init_w = float(user_prof.iloc[0]['initial_weight']) if not user_prof.empty else 70.0
                with c_b1:
                    body_weight = st.number_input("當日體重 (kg)", min_value=30.0, max_value=250.0, value=init_w, step=0.1)
                with c_b2:
                    st.markdown("**🔥 卡路里消耗 (Auto)**")
                    st.info("系統將根據下方各組重量與次數自動計算！")
                    
                mood_val = st.selectbox("心情指數 / 訓練情緒", ["很開心", "開心", "普通", "不開心"])
                st.markdown("---")
                st.markdown("### 🔢 各組重量與次數設定 (Set 1 ~ Set 6)")
                
                sets_config = [
                    ("第一組 (Set 1)", 50.0, 12), ("第二組 (Set 2)", 55.0, 10),
                    ("第三組 (Set 3)", 60.0, 8), ("第四組 (Set 4)", 60.0, 8),
                    ("第五組 (Set 5)", 0.0, 0), ("第六組 (Set 6)", 0.0, 0)
                ]
                
                set_data_input = []
                total_volume = 0.0
                
                for set_name, default_w, default_r in sets_config:
                    cols = st.columns([2, 2, 2])
                    with cols[0]:
                        st.markdown(f"**{set_name}**")
                    with cols[1]:
                        w = st.number_input(f"{set_name} 重量(kg)", min_value=0.0, max_value=500.0, value=default_w, step=2.5, key=f"w_{set_name}")
                    with cols[2]:
                        r = st.number_input(f"{set_name} 次數", min_value=0, max_value=200, value=default_r, step=1, key=f"r_{set_name}")
                    
                    if w > 0 and r > 0:
                        total_volume += (w * r)
                        set_data_input.append({
                            "日期": date_val, "肌群分類": muscle_group, "動作名稱": exercise_name,
                            "組別": set_name, "重量(kg)": w, "次數": r, "體重(kg)": body_weight,
                            "消耗卡路里": 0, "心情指數": mood_val
                        })
                
                estimated_cals = int(100 + (total_volume * 0.06))
                st.success(f"🔥 **預估總訓練量**: {total_volume:.1f} kg ｜ **自動計算消耗卡路里**: ~ {estimated_cals} kcal")
                
                submitted = st.form_submit_button("➕ 批量儲存重量訓練紀錄")
                if submitted:
                    if set_data_input:
                        for item in set_data_input:
                            item["消耗卡路里"] = estimated_cals // len(set_data_input)
                        new_df = pd.DataFrame(set_data_input)
                        updated_df = pd.concat([st.session_state.workout_sets_data, new_df], ignore_index=True)
                        st.session_state.workout_sets_data = validate_and_fix_df(updated_df)
                        save_data(st.session_state.workout_sets_data)
                        st.sidebar.success(f"✅ 成功儲存 {len(set_data_input)} 組紀錄並同步至 GitHub！")
                    else:
                        st.sidebar.warning("⚠️ 請至少填寫一組有效的重量與次數。")

        if st.session_state.username == "admin":
            admin_tab1, admin_tab2 = st.tabs(["👥 所有會員名單與檔案管理", "🛡️ 系統總覽與說明"])
            
            with admin_tab1:
                st.subheader("👥 平台註冊會員與身體檔案管理")
                st.markdown("在此您可以檢視所有註冊會員的基本資料與身體檔案，並可進行線上修改或維護。")
                
                all_users_df = load_users()
                all_profiles_df = load_profiles()
                
                merged_df = pd.merge(all_users_df, all_profiles_df, on="username", how="left")
                
                edited_members = st.data_editor(merged_df, num_rows="dynamic", use_container_width=True, key="admin_member_editor")
                
                if not edited_members.equals(merged_df):
                    new_users_part = edited_members[["username", "password", "name"]]
                    new_profiles_part = edited_members[["username", "height", "initial_weight", "target_weight", "age", "gender", "setup_complete"]]
                    save_users(new_users_part)
                    save_profiles(new_profiles_part)
                    st.success("🔄 會員資料已成功更新並同步至 GitHub！")
                    
            with admin_tab2:
                st.subheader("🛡️ 系統管理員操作說明")
                st.markdown("""
                - **會員管理**：您可以在「所有會員名單與檔案管理」分頁中檢視所有註冊用戶的體重、身高與目標設定。
                - **安全性**：系統採用密碼雜湊加密 (`SHA-256`) 確保會員資料隱私。
                - **資料自動備份**：所有會員的資料均透過 GitHub API 自動即時備份至遠端 Repo，防範雲端休眠洗機。
                """)
        else:
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 詳細圖表分析（互動式圖表）", 
                "📋 所有組數歷史明細", 
                "💡 個人檔案與說明",
                "🤖 AI 報告分析與評分系統"
            ])

            with tab1:
                st.subheader("📈 詳細圖表分析 (Interactive Workout Charts)")
                df = st.session_state.workout_sets_data.sort_values(by="日期")
                
                if not df.empty:
                    selected_mg_filter = st.selectbox("篩選顯示肌群 (Filter by Muscle Group)", ["全部顯示 (All)"] + list(EXERCISE_DICT.keys()) + ["有氧運動 (Cardio)"])
                    if selected_mg_filter != "全部顯示 (All)":
                        df_filtered = df[df["肌群分類"] == selected_mg_filter]
                    else:
                        df_filtered = df
                        
                    col_c1, col_c2 = st.columns(2)
                    
                    with col_c1:
                        st.markdown("#### 1. 肌力提升趨勢圖 (折線圖)")
                        if not df_filtered.empty:
                            df_max_weight = df_filtered.groupby(["日期", "動作名稱"], as_index=False)["重量(kg)"].max()
                            fig_line = px.line(df_max_weight, x="日期", y="重量(kg)", color="動作名稱", markers=True, title="各動作肌力/重量成長曲線")
                            fig_line.update_layout(hovermode="x unified")
                            st.plotly_chart(fig_line, use_container_width=True)
                        else:
                            st.info("此篩選項目尚無數據。")
                            
                    with col_c2:
                        st.markdown("#### 2. 體重與消耗卡路里雙軸圖 (Combo Chart)")
                        df_daily = df.groupby("日期", as_index=False).agg({"體重(kg)": "mean", "消耗卡路里": "max"})
                        fig_combo = go.Figure()
                        fig_combo.add_trace(go.Scatter(x=df_daily['日期'], y=df_daily['體重(kg)'], name="體重 (kg)", mode='lines+markers', line=dict(color='firebrick', width=3)))
                        fig_combo.add_trace(go.Bar(x=df_daily['日期'], y=df_daily['消耗卡路里'], name="每日消耗 (kcal)", opacity=0.4, yaxis='y2'))
                        fig_combo.update_layout(yaxis=dict(title="體重 (kg)"), yaxis2=dict(title="消耗卡路里 (kcal)", overlaying='y', side='right'), hovermode="x unified")
                        st.plotly_chart(fig_combo, use_container_width=True)
                        
                    st.markdown("---")
                    col_c3, col_c4 = st.columns(2)
                    
                    with col_c3:
                        st.markdown("#### 3. 動作次數 / 訓練量比例圖 (圓環圖)")
                        df_action_count = df.groupby("動作名稱", as_index=False)["次數"].sum()
                        fig_donut = px.pie(df_action_count, values="次數", names="動作名稱", hole=0.4, title="各動作完成總次數比例分佈")
                        fig_donut.update_traces(textinfo='percent+label')
                        st.plotly_chart(fig_donut, use_container_width=True)
                        
                    with col_c4:
                        st.markdown("#### 4. 訓練情緒統計圖 (Histogram)")
                        if "心情指數" in df.columns:
                            fig_hist = px.histogram(df, x="心情指數", color="心情指數", title="運動訓練情緒分佈統計", category_orders={"心情指數": ["很開心", "開心", "普通", "不開心"]})
                            st.plotly_chart(fig_hist, use_container_width=True)
                        else:
                            st.info("尚無情緒紀錄。")
                else:
                    st.info("尚無運動紀錄，請由左側輸入或上傳 CSV 檔案。")

            with tab2:
                st.subheader("📋 所有組數詳細紀錄表 (可線上修改，自動存檔)")
                edited_df = st.data_editor(st.session_state.workout_sets_data, num_rows="dynamic", use_container_width=True)
                validated_edited_df = validate_and_fix_df(edited_df)
                
                if not validated_edited_df.equals(st.session_state.workout_sets_data):
                    st.session_state.workout_sets_data = validated_edited_df
                    save_data(validated_edited_df)
                    st.success("🔄 資料已自動更新並同步至 GitHub！")
                
                csv_data = st.session_state.workout_sets_data.to_csv(index=False).encode('utf-8-sig')
                st.download_button(label="📥 下載個人歷史 CSV 紀錄", data=csv_data, file_name=f"workout_history_{st.session_state.username}.csv", mime="text/csv")

            with tab3:
                curr_prof = user_prof.iloc[0]
                st.markdown(f"""
                ### 💡 個人檔案與會員資訊
                - **會員姓名**: {st.session_state.name}
                - **會員帳號**: `{st.session_state.username}`
                - **身高**: {curr_prof['height']} cm
                - **目前體重**: {curr_prof['initial_weight']} kg
                - **目標體重**: {curr_prof['target_weight']} kg
                - **年齡 / 性別**: {curr_prof['age']} 歲 / {curr_prof['gender']}
                """)

            with tab4:
                st.subheader("🤖 AI 智慧身體組成報告分析與詳細處方")
                st.markdown("請上傳 **PDF 體測報告**（支援 InBody 或康文署報告），系統將自動解析數值，並立即產出**詳細報告、AI 綜合評語以及具體的訓練與飲食方向**！")
                
                uploaded_report_file = st.file_uploader("📥 上傳體測報告 (PDF 或 圖片)", type=["pdf", "jpg", "jpeg", "png"])
                
                curr_prof = user_prof.iloc[0]
                extracted_weight = float(curr_prof['initial_weight'])
                extracted_muscle = 28.0
                extracted_fat_p = 20.0
                auto_detected = False
                
                if uploaded_report_file is not None:
                    file_ext = uploaded_report_file.name.split('.')[-1].lower()
                    if file_ext == 'pdf' and HAS_PYPDF:
                        try:
                            reader = pypdf.PdfReader(io.BytesIO(uploaded_report_file.read()))
                            pdf_text = ""
                            for page in reader.pages:
                                pdf_text += page.extract_text() or ""
                            
                            match_w = re.search(r'體重.*?(\d+\.\d+|\d+)', pdf_text)
                            match_m = re.search(r'骨骼肌重.*?(\d+\.\d+|\d+)', pdf_text)
                            match_f = re.search(r'體脂肪率.*?(\d+\.\d+|\d+)', pdf_text)
                            
                            if match_w:
                                extracted_weight = float(match_w.group(1))
                            if match_m:
                                extracted_muscle = float(match_m.group(1))
                            if match_f:
                                extracted_fat_p = float(match_f.group(1))
                                
                            auto_detected = True
                            st.success("🤖 **AI 自動解析成功**：已從 PDF 報告中偵測並代入您的最新體測數據！")
                        except Exception as e:
                            st.warning(f"⚠️ PDF 自動解析失敗，請手動確認下方數值：{e}")
                    elif file_ext in ['jpg', 'jpeg', 'png']:
                        st.image(uploaded_report_file, caption="已上傳的體測報告圖片", use_column_width=True)

                with st.form("report_upload_form"):
                    st.markdown("### 📊 報告數值確認與微調")
                    rep_date = st.date_input("測量日期 Date", datetime.date.today())
                    r_col1, r_col2, r_col3 = st.columns(3)
                    with r_col1:
                        input_weight = st.number_input("測量體重 (kg)", min_value=30.0, max_value=250.0, value=extracted_weight, step=0.1)
                    with r_col2:
                        input_muscle = st.number_input("骨骼肌重 SMM (kg)", min_value=10.0, max_value=100.0, value=extracted_muscle, step=0.1)
                    with r_col3:
                        input_fat_p = st.number_input("體脂肪率 PBF (%)", min_value=3.0, max_value=60.0, value=extracted_fat_p, step=0.1)
                    
                    submit_report = st.form_submit_button("🚀 生成詳細報告與 AI 綜合處方")
                    
                    if submit_report or auto_detected:
                        base_score = 88
                        if input_fat_p > 22:
                            base_score -= int((input_fat_p - 22) * 2)
                        elif input_fat_p < 12:
                            base_score -= int((12 - input_fat_p) * 1)
                        
                        health_score = max(50, min(100, base_score))
                        
                        if health_score >= 88:
                            ai_comment = "🏆 **極佳體態（標準肌肉型）**：您的骨骼肌與體脂肪比例非常優秀，基礎代謝率表現極佳，身體年齡年輕，請持續維持目前的優良習慣！"
                            ai_training = "• **訓練方向**：維持每週 3-4 天重量訓練（著重漸進式超負荷）與 2 天有氧運動，維持肌力與心肺功能。\n• **飲食方向**：維持均衡飲食，每日攝取充足蛋白質（約每公斤體重 1.6g - 1.8g），維持熱量平衡。"
                        elif health_score >= 75:
                            ai_comment = "👍 **良好體態**：肌肉量表現穩定，但體脂肪率可再微幅優化，以呈現更精實的肌肉線條。"
                            ai_training = "• **訓練方向**：增加多關節複合動作（如深蹲、硬舉、臥推），並在重量訓練後穿插 20 分鐘高強度間歇有氧 (HIIT)。\n• **飲食方向**：適度控制精製碳水化合物與含糖飲料，提高蔬菜與優質蛋白質比例。"
                        else:
                            ai_comment = "⚠️ **需要調整**：目前體脂肪率偏高或肌肉量不足，建議透過科學化訓練與飲食控制來進行體態重塑。"
                            ai_training = "• **訓練方向**：以全身性重量訓練為主（每週 4 天），刺激全身肌肉生長以拉高基礎代謝率。\n• **飲食方向**：實施微幅熱量赤字（減少 200-300 kcal），嚴格控制油脂與糖分攝取。"

                        new_rep_row = pd.DataFrame([{
                            "測量日期": rep_date,
                            "體重(kg)": input_weight,
                            "骨骼肌重(kg)": input_muscle,
                            "體脂肪率(%)": input_fat_p,
                            "健康分數": health_score,
                            "AI評語": f"{ai_comment}\n\n{ai_training}"
                        }])
                        
                        st.session_state.body_reports_data = pd.concat([st.session_state.body_reports_data, new_rep_row], ignore_index=True).drop_duplicates(subset=["測量日期"], keep="last")
                        save_reports(st.session_state.body_reports_data)
                        
                        st.markdown("---")
                        st.markdown("### 📋 【🤖 AI 教練詳細報告與處方】")
                        st.success(f"🎉 報告分析完成！本次 AI 綜合健康評分：**{health_score} 分**")
                        st.info(f"**【AI 綜合評語】**\n\n{ai_comment}")
                        st.warning(f"**【詳細訓練與飲食方向】**\n\n{ai_training}")
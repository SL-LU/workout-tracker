import streamlit as st
import pandas as pd
import datetime
import os
import hashlib
import plotly.express as px
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(
    page_title="專業多組重量訓練追蹤系統 (會員登入版)",
    page_icon="🏋️‍♂️",
    layout="wide"
)

# 密碼雜湊輔助函式
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 預設帳號密碼資料庫 (預設管理員帳號: admin / 密碼: 123456)
USER_DB_FILE = "users_db.csv"

def load_users():
    if os.path.exists(USER_DB_FILE):
        try:
            return pd.read_csv(USER_DB_FILE)
        except:
            pass
    # 預設帳號
    default_users = pd.DataFrame([
        {"username": "admin", "password": hash_password("123456"), "name": "系統管理員"},
        {"username": "coach", "password": hash_password("coach888"), "name": "專業教練"}
    ])
    default_users.to_csv(USER_DB_FILE, index=False)
    return default_users

def save_users(users_df):
    users_df.to_csv(USER_DB_FILE, index=False)

# 初始化登入狀態
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
                    st.success(f"歡迎回來，{st.session_state.name}！正在進入系統...")
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
                    st.success("✅ 註冊成功！請切換至「登入系統」分頁進行登入。")

# ----------------- 登入後的健身追蹤主程式 -----------------
else:
    # 頂端導覽列與登出按鈕
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

    # 每個用戶專屬的資料檔案
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
        # 預設範例資料
        return pd.DataFrame([
            {
                "日期": datetime.date(2026, 10, 10),
                "肌群分類": "胸部 (Chest)",
                "動作名稱": "槓鈴平地臥推 (Barbell Bench Press)",
                "組別": "第一組 (Set 1)",
                "重量(kg)": 50.0,
                "次數": 12,
                "體重(kg)": 70.5,
                "消耗卡路里": 180,
                "心情指數": "開心"
            },
            {
                "日期": datetime.date(2026, 10, 12),
                "肌群分類": "腿部 (Legs)",
                "動作名稱": "槓鈴深蹲 (Barbell Squat)",
                "組別": "第一組 (Set 1)",
                "重量(kg)": 80.0,
                "次數": 10,
                "體重(kg)": 70.2,
                "消耗卡路里": 220,
                "心情指數": "普通"
            }
        ])

    def save_data(df):
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

    if 'workout_sets_data' not in st.session_state:
        st.session_state.workout_sets_data = load_data()

    # 完整健身動作選單庫
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

    # 側邊欄 - CSV 匯入與表單
    st.sidebar.header(f"👤 當前用戶: {st.session_state.name}")
    
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
        muscle_group = st.sidebar.selectbox("選擇主肌群 Muscle Group", list(EXERCISE_DICT.keys()))
        
        available_exercises = EXERCISE_DICT[muscle_group]
        exercise_name = st.selectbox("動作名稱 Exercise Name", available_exercises + ["其他自訂 (Other)"])
        if exercise_name == "其他自訂 (Other)":
            exercise_name = st.text_input("請輸入自訂動作名稱", "自訂動作")
        
        c_b1, c_b2 = st.columns(2)
        with c_b1:
            body_weight = st.number_input("當日體重 (kg)", min_value=30.0, max_value=250.0, value=70.0, step=0.1)
        with c_b2:
            cals_burned = st.number_input("每日消耗 (kcal)", min_value=0, max_value=5000, value=200, step=10)
            
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
        ]
        
        set_data_input = []
        for set_name, default_w, default_r in sets_config:
            cols = st.columns([2, 2, 2])
            with cols[0]:
                st.markdown(f"**{set_name}**")
            with cols[1]:
                w = st.number_input(f"{set_name} 重量(kg)", min_value=0.0, max_value=500.0, value=default_w, step=2.5, key=f"w_{set_name}")
            with cols[2]:
                r = st.number_input(f"{set_name} 次數", min_value=0, max_value=200, value=default_r, step=1, key=f"r_{set_name}")
            
            if w > 0 and r > 0:
                set_data_input.append({
                    "日期": date_val,
                    "肌群分類": muscle_group,
                    "動作名稱": exercise_name,
                    "組別": set_name,
                    "重量(kg)": w,
                    "次數": r,
                    "體重(kg)": body_weight,
                    "消耗卡路里": cals_burned,
                    "心情指數": mood_val
                })
                
        submitted = st.form_submit_button("➕ 批量儲存所有組數紀錄")
        if submitted:
            if set_data_input:
                new_df = pd.DataFrame(set_data_input)
                st.session_state.workout_sets_data = pd.concat([st.session_state.workout_sets_data, new_df], ignore_index=True)
                save_data(st.session_state.workout_sets_data)
                st.sidebar.success(f"✅ 成功儲存 {len(set_data_input)} 組紀錄並已自動存檔！")
            else:
                st.sidebar.warning("⚠️ 請至少填寫一組有效的重量與次數。")

    # 主頁面分頁
    tab1, tab2, tab3 = st.tabs(["📊 詳細圖表分析（互動式圖表）", "📋 所有組數歷史明細", "💡 會員系統與功能說明"])

    with tab1:
        st.subheader("📈 詳細圖表分析 (Interactive Workout Charts)")
        df = st.session_state.workout_sets_data.sort_values(by="日期")
        
        if not df.empty:
            selected_mg_filter = st.selectbox("篩選顯示肌群 (Filter by Muscle Group)", ["全部顯示 (All)"] + list(EXERCISE_DICT.keys()))
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
                    st.info("此肌群尚無數據。")
                    
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
        if not edited_df.equals(st.session_state.workout_sets_data):
            st.session_state.workout_sets_data = edited_df
            save_data(edited_df)
            st.success("🔄 資料已自動更新並存檔！")
        
        csv_data = st.session_state.workout_sets_data.to_csv(index=False).encode('utf-8-sig')
        st.download_button(label="📥 下載個人歷史 CSV 紀錄", data=csv_data, file_name=f"workout_history_{st.session_state.username}.csv", mime="text/csv")

    with tab3:
        st.markdown(f"""
        ### 💡 會員登入系統說明
        - **當前登入用戶**：`{st.session_state.name}` (`{st.session_state.username}`)
        - **獨立數據隔離**：每位登入的用戶都擁有專屬的資料存檔檔案 (`workout_data_{st.session_state.username}.csv`)，資料完全獨立、互不干擾。
        - **預設管理員帳號**：
          - 帳號：`admin` / 密碼：`123456`
          - 帳號：`coach` / 密碼：`coach888`
        - 您也可以隨時切換到「註冊新帳號」分頁建立店面員工或新會員的專屬帳號！
        """)

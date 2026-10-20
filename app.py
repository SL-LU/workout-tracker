import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
import plotly.graph_objects as go

# 頁面基本配置
st.set_page_config(
    page_title="全方位專業健身與進度分析系統",
    page_icon="🏋️‍♂️",
    layout="wide"
)

st.title("🏋️‍♂️ 全方位個人健身紀錄與進度追蹤系統 (CSV 匯入與互動圖表旗艦版)")
st.markdown("本系統支援 **CSV 歷史資料匯入**、**自動本地存檔**，以及完整的 **4 大互動式進度圖表分析**！")

# 資料檔案路徑
DATA_FILE = "workout_persistent_data.csv"

# 預設動作資料庫
EXERCISE_DICT = {
    "胸部 (Chest)": [
        "槓鈴平地臥推 (Barbell Bench Press)",
        "啞鈴平地臥推 (Dumbbell Bench Press)",
        "上斜槓鈴臥推 (Incline Barbell Bench Press)",
        "上斜啞鈴臥推 (Incline Dumbbell Bench Press)",
        "下斜臥推 (Decline Bench Press)",
        "胸推機 (Chest Press Machine)",
        "夾胸機 / 蝴蝶機 (Chest Fly / Pec Deck)",
        "Cable 繩索夾胸 (Cable Crossover)",
        "伏地挺身 (Push-ups)",
        "雙槓臂屈伸 (Chest Dips)"
    ],
    "背部 (Back)": [
        "傳統硬舉 (Conventional Deadlift)",
        "相撲硬舉 (Sumo Deadlift)",
        "引體向上 (Pull-ups)",
        "高位下拉 (Lat Pulldown)",
        "槓鈴俯身划船 (Barbell Row)",
        "單臂啞鈴划船 (Dumbbell Row)",
        "T-Bar 划船 (T-Bar Row)",
        "坐姿滑輪划船 (Seated Cable Row)",
        "直臂下壓 (Straight Arm Pulldown)",
        "反向飛鳥 / 划船 (Rear Delt Fly)"
    ],
    "腿部 (Legs)": [
        "槓鈴深蹲 (Barbell Squat)",
        "前蹲舉 (Front Squat)",
        "保加利亞分腿蹲 (Bulgarian Split Squat)",
        "腿部推舉機 (Leg Press)",
        "羅馬尼亞硬舉 (Romanian Deadlift)",
        "箱式深蹲 (Box Squat)",
        "腿屈伸機 (Leg Extension)",
        "俯臥腿彎舉 (Leg Curl)",
        "坐姿提踵 (Seated Calf Raise)",
        "站姿提踵 (Standing Calf Raise)",
        "臀橋 / 臀推 (Hip Thrust)"
    ],
    "肩膀 (Shoulders)": [
        "站姿槓鈴肩推 (Overhead Press)",
        "坐姿啞鈴肩推 (Dumbbell Shoulder Press)",
        "啞鈴側平舉 (Lateral Raise)",
        "Cable 側平舉 (Cable Lateral Raise)",
        "啞鈴前平舉 (Front Raise)",
        "面拉 (Face Pull)",
        "阿諾肩推 (Arnold Press)",
        "直立划船 (Upright Row)"
    ],
    "手臂 (Arms)": [
        "槓鈴二頭彎舉 (Barbell Bicep Curl)",
        "啞鈴二頭彎舉 (Dumbbell Bicep Curl)",
        "錘式彎舉 (Hammer Curl)",
        "牧師凳彎舉 (Preacher Curl)",
        "Cable 二頭彎舉 (Cable Curl)",
        "三頭下壓 (Triceps Pushdown)",
        "仰臥三頭臂屈伸 / 骷髏碎者 (Skull Crusher)",
        "過頭啞鈴三頭伸展 (Overhead Dumbbell Extension)",
        "雙槓三頭支撐 (Triceps Dips)"
    ],
    "核心 (Core)": [
        "棒式 / 平板支撐 (Plank)",
        "側棒式 (Side Plank)",
        "仰臥起坐 / 捲腹 (Crunch)",
        "懸垂舉腿 (Hanging Leg Raise)",
        "俄羅斯轉體 (Russian Twist)",
        "健腹輪 (Ab Wheel Rollout)",
        "仰臥抬腿 (Leg Raises)",
        "鳥狗式 (Bird-Dog)"
    ],
    "有氧運動 (Cardio)": [
        "跑步機跑步 (Treadmill Running)",
        "室內固定式腳踏車 (Stationary Bike)",
        "橢圓機 (Elliptical Trainer)",
        "划船機 (Rowing Machine)",
        "階梯機 (Stair Climber)",
        "跳繩 (Jump Rope)",
        "高強度間歇訓練 HIIT"
    ]
}

# 讀取與儲存資料函式
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            if "日期" in df.columns:
                df["日期"] = pd.to_datetime(df["日期"]).dt.date
            return df
        except Exception as e:
            st.error(f"讀取存檔失敗: {e}")
    
    # 預設初始示範資料
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
            "重量(kg)": 75.0,
            "次數": 10,
            "體重(kg)": 70.2,
            "消耗卡路里": 220,
            "心情指數": "普通"
        },
        {
            "日期": datetime.date(2026, 10, 15),
            "肌群分類": "胸部 (Chest)",
            "動作名稱": "槓鈴平地臥推 (Barbell Bench Press)",
            "組別": "第二組 (Set 2)",
            "重量(kg)": 60.0,
            "次數": 8,
            "體重(kg)": 70.0,
            "消耗卡路里": 200,
            "心情指數": "很開心"
        },
        {
            "日期": datetime.date(2026, 10, 18),
            "肌群分類": "腿部 (Legs)",
            "動作名稱": "槓鈴深蹲 (Barbell Squat)",
            "組別": "第二組 (Set 2)",
            "重量(kg)": 85.0,
            "次數": 8,
            "體重(kg)": 69.8,
            "消耗卡路里": 250,
            "心情指數": "很開心"
        }
    ])

def save_data(df):
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

if 'workout_sets_data' not in st.session_state:
    st.session_state.workout_sets_data = load_data()

# ================= 側邊欄：匯入 CSV 與 逐組新增紀錄 =================
st.sidebar.header("📥 匯入歷史 CSV 資料")
uploaded_file = st.sidebar.file_content = st.sidebar.file_uploader("上傳 CSV 備份檔案", type=["csv"])

if uploaded_file is not None:
    try:
        imported_df = pd.read_csv(uploaded_file)
        if "日期" in imported_df.columns:
            imported_df["日期"] = pd.to_datetime(imported_df["日期"]).dt.date
        
        if st.sidebar.button("覆蓋/合併匯入資料"):
            st.session_state.workout_sets_data = pd.concat([st.session_state.workout_sets_data, imported_df], ignore_index=True).drop_duplicates()
            save_data(st.session_state.workout_sets_data)
            st.sidebar.success("✅ CSV 資料成功匯入並已自動存檔！")
    except Exception as e:
        st.sidebar.error(f"匯入失敗: {e}")

st.sidebar.markdown("---")
st.sidebar.header("📝 逐組輸入今日訓練紀錄")

with st.sidebar.form("multiset_form", clear_on_submit=False):
    date_val = st.date_input("日期 Date", datetime.date.today())
    muscle_group = st.sidebar.selectbox("選擇主肌群 Muscle Group", list(EXERCISE_DICT.keys()))
    
    available_exercises = EXERCISE_DICT[muscle_group]
    exercise_name = st.selectbox("動作名稱 Exercise Name", available_exercises + ["其他自訂 (Other)"])
    if exercise_name == "其他自訂 (Other)":
        exercise_name = st.text_input("請輸入自訂動作名稱", "自訂動作")
    
    body_weight = st.number_input("當日體重 (kg)", min_value=30.0, max_value=250.0, value=70.0, step=0.1)
    cals_burned = st.number_input("每日消耗卡路里 (kcal)", min_value=0, max_value=5000, value=200, step=10)
    mood_val = st.selectbox("訓練心情 MOOD", ["很開心", "開心", "普通", "不開心"])
    
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
            
    submitted = st.form_submit_button("➕ 儲存今日所有組數紀錄")
    if submitted:
        if set_data_input:
            new_df = pd.DataFrame(set_data_input)
            st.session_state.workout_sets_data = pd.concat([st.session_state.workout_sets_data, new_df], ignore_index=True)
            save_data(st.session_state.workout_sets_data)
            st.sidebar.success(f"✅ 成功儲存 {len(set_data_input)} 組紀錄並自動備份！")
        else:
            st.sidebar.warning("⚠️ 請至少填寫一組有效的重量與次數。")

# ================= 主畫面：4 大詳細圖表分析 & 歷史資料 =================
tab1, tab2, tab3 = st.tabs(["📊 詳細圖表分析 (互動式)", "📋 歷史資料與 CSV 導出", "💡 系統使用說明"])

with tab1:
    st.subheader("📈 互動式圖表分析面板")
    df = st.session_state.workout_sets_data.sort_values(by="日期")
    
    if not df.empty:
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.markdown("#### 1. 肌力提升趨勢圖（折線圖 Line Chart）")
            st.caption("依動作類別自動折線，觀察臥推、深蹲等重量與體重成長曲線。")
            selected_mg = st.selectbox("選擇篩選肌群", ["全部肌群 (All)"] + list(EXERCISE_DICT.keys()))
            
            if selected_mg != "全部肌群 (All)":
                df_chart1 = df[df["肌群分類"] == selected_mg]
            else:
                df_chart1 = df
                
            if not df_chart1.empty:
                fig_strength = px.line(
                    df_chart1,
                    x="日期",
                    y="重量(kg)",
                    color="動作名稱",
                    markers=True,
                    title="各動作重量成長趨勢"
                )
                fig_strength.update_layout(hovermode="x unified")
                st.plotly_chart(fig_strength, use_container_width=True)
            else:
                st.info("此肌群無相關資料。")
                
        with col_c2:
            st.markdown("#### 2. 體重與卡路里雙軸圖（Combo Chart）")
            st.caption("同時對比體重變化與每日消耗卡路里相關性。")
            
            # 以日期聚合成每日代表資料
            df_daily = df.groupby("日期", as_index=False).agg({
                "體重(kg)": "mean",
                "消耗卡路里": "mean"
            })
            
            fig_combo = go.Figure()
            fig_combo.add_trace(go.Scatter(
                x=df_daily['日期'],
                y=df_daily['體重(kg)'],
                name="體重 (kg)",
                mode='lines+markers',
                line=dict(color='firebrick', width=3)
            ))
            fig_combo.add_trace(go.Bar(
                x=df_daily['日期'],
                y=df_daily['消耗卡路里'],
                name="消耗卡路里 (kcal)",
                opacity=0.4,
                yaxis='y2'
            ))
            
            fig_combo.update_layout(
                title="體重 vs 每日消耗卡路里趨勢",
                yaxis=dict(title="體重 (kg)"),
                yaxis2=dict(title="消耗卡路里 (kcal)", overlaying='y', side='right'),
                hovermode="x unified",
                legend=dict(x=0.01, y=0.99)
            )
            st.plotly_chart(fig_combo, use_container_width=True)
            
        st.markdown("---")
        col_c3, col_c4 = st.columns(2)
        
        with col_c3:
            st.markdown("#### 3. 動作次數比例圖（圓環圖 Donut Chart）")
            st.caption("視覺化呈現不同訓練項目的次數與活動總量占比。")
            
            fig_donut = px.pie(
                df,
                names="動作名稱",
                values="次數",
                hole=0.4,
                title="各動作累積次數比例 (Donut Chart)"
            )
            st.plotly_chart(fig_donut, use_container_width=True)
            
        with col_c4:
            st.markdown("#### 4. 訓練情緒統計圖（直方圖 Histogram）")
            st.caption("統計運動時的心情分佈狀況。")
            
            fig_mood = px.histogram(
                df,
                x="心情指數",
                color="心情指數",
                title="訓練情緒數量統計 (Mood Distribution)"
            )
            st.plotly_chart(fig_mood, use_container_width=True)
            
    else:
        st.info("目前尚無運動紀錄，請由左側輸入或匯入 CSV 檔案。")

with tab2:
    st.subheader("📋 所有歷史紀錄列表 (可線上編輯並存檔)")
    edited_df = st.data_editor(
        st.session_state.workout_sets_data,
        num_rows="dynamic",
        use_container_width=True
    )
    
    if not edited_df.equals(st.session_state.workout_sets_data):
        st.session_state.workout_sets_data = edited_df
        save_data(edited_df)
        st.success("🔄 資料修改已自動更新並保存至本地檔案！")
    
    csv_data = st.session_state.workout_sets_data.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 下載完整 CSV 紀錄檔案 (導出)",
        data=csv_data,
        file_name="workout_records_backup.csv",
        mime="text/csv"
    )

with tab3:
    st.markdown("""
    ### 💡 旗艦版功能說明
    1. **CSV 匯入功能**：左側側邊欄支援直接上傳過去備份的 CSV 檔案，快速恢復歷史紀錄。
    2. **4 大互動式詳細圖表**：
       - **肌力提升趨勢圖（折線圖）**：精準追蹤臥推、深蹲等項目的重量成長曲線。
       - **體重與卡路里雙軸圖（Combo Chart）**：折線（體重）與柱狀圖（消耗卡路里）同時呈現。
       - **動作次數比例圖（圓環圖）**：查看各個動作佔總訓練次數的比例。
       - **訓練情緒統計圖（Histogram）**：統計運動時的心情分佈。
    3. **本地永久自動存檔**：所有修改皆會寫入 `workout_persistent_data.csv`，關閉終端機或重啟網頁資料都不會丟失。
    """)

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
                
                # 1. 肌力提升趨勢圖
                with col_c1:
                    st.markdown("#### 1. 肌力提升趨勢圖 (折線圖)")
                    if not df_filtered.empty:
                        df_max_weight = df_filtered.groupby(["日期", "動作名稱"], as_index=False)["重量(kg)"].max()
                        fig_line = px.line(df_max_weight, x="日期", y="重量(kg)", color="動作名稱", markers=True, title="各動作肌力/重量成長曲線")
                        fig_line.update_layout(hovermode="x unified")
                        st.plotly_chart(fig_line, use_container_width=True)
                    else:
                        st.info("此肌群尚無數據。")
                    
                # 2. 體重與消耗卡路里雙軸圖
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
                
                # 3. 動作次數比例圖 (圓環圖)
                with col_c3:
                    st.markdown("#### 3. 動作次數 / 訓練量比例圖 (圓環圖)")
                    df_action_count = df.groupby("動作名稱", as_index=False)["次數"].sum()
                    fig_donut = px.pie(df_action_count, values="次數", names="動作名稱", hole=0.4, title="各動作完成總次數比例分佈")
                    fig_donut.update_traces(textinfo='percent+label')
                    st.plotly_chart(fig_donut, use_container_width=True)
                
                # 4. 訓練情緒統計圖
                with col_c4:
                    st.markdown("#### 4. 訓練情緒統計圖 (Histogram)")
                    if "心情指數" in df.columns:
                        fig_hist = px.histogram(df, x="心情指數", color="心情指數", title="運動訓練情緒分佈統計", category_orders={"心情指數": ["很開心", "開心", "普通", "不開心"]})
                        st.plotly_chart(fig_hist, use_container_width=True)
                    else:
                        st.info("尚無情緒紀錄。")
            else:
                st.info("尚無運動紀錄，請由左側輸入或上傳 CSV 檔案。")
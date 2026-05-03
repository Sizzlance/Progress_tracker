import streamlit as st
import pandas as pd
import datetime
from database import *

init_db()

st.set_page_config(page_title="Pro-Tracker", layout="wide", page_icon="🏋️‍♂️")

st.sidebar.title("Navigation")
menu = st.sidebar.selectbox("Меню", ["Тренировка", "Настройка программы", "Аналитика"])

if menu == "Настройка программы":
    st.header("⚙️ Управление программой")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Создать день")
        day_name = st.text_input("Название (напр., Понедельник)", key="new_day_input")
        if st.button("Создать день"):
            if day_name:
                add_training_day(day_name)
                st.success(f"День '{day_name}' создан")
                st.rerun()

    with col2:
        st.subheader("2. Добавить упражнение")
        ex_name = st.text_input("Название (напр., Жим лежа)", key="new_ex_input")
        if st.button("Добавить в базу"):
            if ex_name:
                add_exercise(ex_name)
                st.success(f"'{ex_name}' добавлено в список")
                st.rerun()

    st.divider()

    st.subheader("3. Состав тренировочных дней")
    all_days = get_training_days()
    all_exercises = get_exercises()

    if all_days and all_exercises:
        c1, c2 = st.columns([1, 2])
        with c1:
            sel_day = st.selectbox("Выбери день", all_days)
        with c2:
            sel_ex = st.multiselect("Добавь упражнения в этот день", all_exercises)

        if st.button("Привязать упражнения"):
            for e in sel_ex:
                link_exercise_to_day(sel_day, e)
            st.success("Обновлено!")
            st.rerun()

    if all_days:
        st.write(f"**Текущие упражнения в дне: {sel_day}**")
        current_exercises = get_exercises_by_day(sel_day)
        if not current_exercises:
            st.info("В этом дне пока нет упражнений.")
        else:
            for ex in current_exercises:
                col_ex, col_btn = st.columns([4, 1])
                col_ex.write(f"• {ex}")
                if col_btn.button("Удалить", key=f"del_{sel_day}_{ex}"):
                    remove_exercise_from_day(sel_day, ex)
                    st.rerun()

elif menu == "Тренировка":
    st.header("💪 Тренировочная сессия")
    all_days = get_training_days()

    if not all_days:
        st.warning("Сначала создай тренировочный день в 'Настройке программы'")
    else:
        col_date, col_day = st.columns(2)
        with col_date:
            selected_date = st.date_input("Дата тренировки", datetime.date.today())
        with col_day:
            current_day = st.selectbox("Тренировочный день", all_days)

        day_exercises = get_exercises_by_day(current_day)

        if not day_exercises:
            st.info("Добавь упражнения в этот день в настройках.")
        else:
            selected_exercise = st.selectbox("Выбери упражнение", day_exercises)

            st.divider()

            num_sets = st.number_input("Сколько подходов будем делать?", min_value=1, max_value=15, value=3, step=1)

            with st.form("dynamic_log_form", clear_on_submit=True):
                st.write("Запиши вес и повторения для каждого подхода:")
                sets_data = []

                for i in range(num_sets):
                    c1, c2, c3 = st.columns([1, 2, 2])
                    c1.markdown(f"<div style='margin-top: 30px;'><b>Подход {i + 1}</b></div>", unsafe_allow_html=True)
                    w = c2.number_input("Вес (кг)", min_value=0.0, step=0.5, format="%.1f", key=f"weight_{i}")
                    r = c3.number_input("Повторы", min_value=1, step=1, value=10, key=f"reps_{i}")
                    sets_data.append({"weight": w, "reps": r})

                submitted = st.form_submit_button("💾 Записать все подходы")

                if submitted:
                    for s in sets_data:
                        save_log(selected_exercise, s["weight"], s["reps"], selected_date)

                    st.success(f"Успешно сохранено {num_sets} подходов за {selected_date.strftime('%d.%m.%Y')}!")
                    st.rerun()

            st.divider()
            df = get_logs_df(selected_exercise)

            if not df.empty:
                tab1, tab2 = st.tabs(["📈 График прогресса", "📜 История и удаление"])

                with tab1:
                    df_chart = df.copy()
                    df_chart['date'] = pd.to_datetime(df_chart['date']).dt.strftime('%Y-%m-%d')

                    chart_data = df_chart.groupby('date')['weight'].max()

                    st.line_chart(chart_data)

                with tab2:
                    for index, row in df.iterrows():
                        r1, r2, r3, r4 = st.columns([2, 2, 2, 1])
                        r1.write(f"{row['date']}")
                        r2.write(f"**{row['weight']} кг**")
                        r3.write(f"{row['reps']} повт.")
                        if r4.button("🗑️", key=f"log_del_{row['id']}"):
                            delete_log(row['id'])
                            st.rerun()
            else:
                st.write("История подходов пуста.")

elif menu == "Аналитика":
    st.header("📊 Углубленная аналитика")

    df_all = get_all_logs_df()

    if df_all.empty:
        st.info("Данных пока нет. Начни тренироваться!")
    else:
        df_all['tonnage'] = df_all['weight'] * df_all['reps']
        df_all['date'] = pd.to_datetime(df_all['date']).dt.strftime('%Y-%m-%d')

        days_list = ["Все дни"] + list(df_all['training_day'].dropna().unique())
        selected_day_filter = st.selectbox("Фильтр по дню программы", days_list)

        df_filtered = df_all.copy()
        if selected_day_filter != "Все дни":
            df_filtered = df_all[df_all['training_day'] == selected_day_filter]

        col1, col2, col3 = st.columns(3)
        total_tonnage = df_filtered['tonnage'].sum()
        total_sets = len(df_filtered)
        avg_intensity = df_filtered['weight'].mean() if not df_filtered.empty else 0

        col1.metric("Общий тоннаж", f"{total_tonnage:,.0f} кг")
        col2.metric("Всего подходов", total_sets)
        col3.metric("Средний вес", f"{avg_intensity:.1f} кг")

        st.divider()

        tab_vol, tab_exercises = st.tabs(["📈 Динамика объема", "🏋️ Анализ упражнений"])

        with tab_vol:
            st.subheader(f"Прогресс объема: {selected_day_filter}")
            daily_stats = df_filtered.groupby('date').agg({
                'tonnage': 'sum',
                'weight': 'mean'
            }).sort_index()

            st.line_chart(daily_stats['tonnage'])

            if st.checkbox("Показать график интенсивности (средний вес)"):
                st.line_chart(daily_stats['weight'])

        with tab_exercises:
            st.subheader("Статистика по конкретным упражнениям")
            ex_stats = df_filtered.groupby('exercise').agg({
                'tonnage': 'sum',
                'weight': ['max', 'mean'],
                'reps': 'count'
            })
            ex_stats.columns = ['Общий объем (кг)', 'Max вес (кг)', 'Ср. вес (кг)', 'Подходов']
            st.dataframe(ex_stats.sort_values(by='Общий объем (кг)', ascending=False), width=True)

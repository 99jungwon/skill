import streamlit as st
import pandas as pd

excel_file = "skill.xlsx"
sheet_map = {"타자": "Skill_타자", "투수": "Skill_투수"}

# 포지션
position = st.selectbox("포지션 선택", list(sheet_map.keys()))
sheet_name = sheet_map[position]
df = pd.read_excel(excel_file, sheet_name=sheet_name)
df.columns = df.columns.str.strip()

# 카드 등급(분류)
grades = df["분류"].dropna().unique()
grade = st.selectbox("카드 종류(등급) 선택", grades)
filtered = df[df["분류"] == grade]

# (투수일 때만 보직)
if position == "투수" and "보직" in df.columns:
    all_jobs = df["보직"].dropna().unique()
    show_jobs = [j for j in all_jobs if str(j).strip() != ""]
    show_jobs.append("없음/공통")
    job = st.selectbox("보직 선택", show_jobs)
    if job == "없음/공통":
        job = None
else:
    job = None

st.markdown("※ 스킬명은 띄어쓰기 없이 정확히 입력해 주세요.")

# 스킬/레벨 입력
skill_inputs = []
level_inputs = []
for i in range(3):
    skill = st.text_input(f"스킬{i+1} 이름", key=f"skill{i+1}")
    level = st.number_input(f"스킬{i+1} 레벨 (5~8)", min_value=5, max_value=8, step=1, key=f"level{i+1}")
    skill_inputs.append(skill.strip())
    level_inputs.append(level)

# 우선순위별 필터 함수
def filter_skill(df, skill, level, grade, job):
    has_job = "보직" in df.columns
    has_grade = "분류" in df.columns

    # 1. 등급+보직
    if has_grade and has_job and job is not None:
        row = df[
            (df["스킬명"] == skill) &
            (df["레벨"] == level) &
            (df["분류"] == grade) &
            (df["보직"] == job)
        ]
        if not row.empty:
            return row, "등급+보직 일치"
    # 2. 등급만
    if has_grade:
        if has_job:
            row = df[
                (df["스킬명"] == skill) &
                (df["레벨"] == level) &
                (df["분류"] == grade) &
                (df["보직"].isna() | (df["보직"] == ""))
            ]
        else:
            row = df[
                (df["스킬명"] == skill) &
                (df["레벨"] == level) &
                (df["분류"] == grade)
            ]
        if not row.empty:
            return row, "등급만 일치"
    # 3. 보직만
    if has_job and job is not None:
        row = df[
            (df["스킬명"] == skill) &
            (df["레벨"] == level) &
            (df["보직"] == job)
        ]
        if not row.empty:
            return row, "보직만 일치"
    # 4. 완전 공통
    row = df[
        (df["스킬명"] == skill) &
        (df["레벨"] == level)
    ]
    if not row.empty:
        return row, "공통"
    # 없으면 empty
    return pd.DataFrame(), None


# 결과 계산
if st.button(f"{position} 결과 계산"):
    sum_stats = {"파워": 0, "정확": 0, "선구": 0, "구위": 0, "변화": 0}
    details = []

    for idx, (skill, level) in enumerate(zip(skill_inputs, level_inputs), 1):
        row, how = filter_skill(df, skill, level, grade, job)
        if row.empty:
            details.append(f"스킬{idx}: '{skill}'(레벨 {level}) 조합 없음")
        else:
            if position == "타자":
                p, a, s = row.iloc[0].get("파워", 0), row.iloc[0].get("정확", 0), row.iloc[0].get("선구", 0)
                details.append(f"스킬{idx}: {how} → 파워 {p}, 정확 {a}, 선구 {s}")
                sum_stats["파워"] += p if not pd.isna(p) else 0
                sum_stats["정확"] += a if not pd.isna(a) else 0
                sum_stats["선구"] += s if not pd.isna(s) else 0
            else:
                g, c = row.iloc[0].get("구위", 0), row.iloc[0].get("변화", 0)
                details.append(f"스킬{idx}: {how} → 구위 {g}, 변화 {c}")
                sum_stats["구위"] += g if not pd.isna(g) else 0
                sum_stats["변화"] += c if not pd.isna(c) else 0

    st.subheader("입력된 각 스킬별 증가량")
    for d in details:
        st.write(d)

    st.markdown("---")
    st.subheader(f"스킬 3개 합산 {position} 능력치 증가 총합")

    # 결과 테이블 만들기
    if position == "타자":
        stat_table = {
            "파워 + 정확 합": [sum_stats["파워"] + sum_stats["정확"]],
            "파워 + 정확 + 선구 합": [sum_stats["파워"] + sum_stats["정확"] + sum_stats["선구"]],
        }
        st.table(pd.DataFrame(stat_table))
    else:
        stat_table = {
            "구위 + 변화 합": [sum_stats["구위"] + sum_stats["변화"]],
        }
        st.table(pd.DataFrame(stat_table))

    # 개별 합도 출력(원한다면)
    if position == "타자":
        st.write(f"**파워 합:** {sum_stats['파워']}")
        st.write(f"**정확 합:** {sum_stats['정확']}")
        st.write(f"**선구 합:** {sum_stats['선구']}")
    else:
        st.write(f"**구위 합:** {sum_stats['구위']}")
        st.write(f"**변화 합:** {sum_stats['변화']}")


with st.expander("🔔 주의사항", expanded=True):
    st.markdown("""
    - **스킬명은 띄어쓰기를 하지 않고 입력해야 합니다.**
    - **스킬 레벨은 5~8레벨까지만 입력이 가능합니다.**
    - 모든 스킬은 랭킹챌린지를 기준으로 하였습니다.
    - 확률적 발동 스킬은 적절히 계산한 기대값을 반영하였습니다. ([참조](https://docs.google.com/spreadsheets/d/1kZAuq55_F0cNyeGBUCNIvvVclsarapLQ/edit?gid=17427492#gid=17427492))  
    - 방깎 스킬(마당쇠, 저니맨 등)의 경우 파정과 변구의 가치를 동등하게 반영하였습니다.
    - 해당 위치 배치가 필요한 스킬(공포의 하위타선, 원투펀치 등)의 경우 배치가 되었음을 가정하였습니다.
    - 국대에이스와 포수리드의 전체 버프 효과는 제외하였습니다.
    - 승리조와 패전조의 차이를 두지 않았습니다.
    """)

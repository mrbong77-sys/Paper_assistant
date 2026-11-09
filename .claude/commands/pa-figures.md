---
description: S6 — 표·그림 예산을 정하고 스크립트로 만들어 해상도와 형식을 점검합니다.
argument-hint: [slug]
---

S6 시각화. 산출물은 `06_figures/figures.md`, `06_figures/scripts/`, `06_figures/out/`입니다. 규칙은 DI-01–DI-10.

1. **예산.** 저널 상한(`01_topic/journal.md`) 안에서 표·그림 목록을 정합니다. 하나에 메시지 하나(한 문장). 같은 자료를 표와 그림에 겹치지 않습니다. 예산표를 사람에게 보여 줍니다.
2. **형태 고르기.** 반복 수치는 표, 추세·관계·분포는 그림. 비교는 같은 축, 정렬된 순서. 데이터 시각화 지침이 있으면(예: dataviz 스킬) 따릅니다.
3. **스크립트.** 그림마다 스크립트 하나(`06_figures/scripts/figN_<이름>.py`). 수치 원장이나 `05_data/processed/`만 읽습니다.
   ```python
   from pa.figures import apply_style, save
   apply_style()          # 가는 선(0.6 pt), 작은 표식, 8 pt 글꼴, 색맹 안전 팔레트 + 선 모양·표식 순환
   fig, ax = plt.subplots(figsize=(3.4, 2.4))   # 단 폭에 맞춤
   ...
   save(fig, "06_figures/out/fig2_accuracy")    # PDF + 600 dpi PNG
   ```
   - 겹치는 계열은 선을 더 가늘게, 밀집 구역은 확대 삽입도로. 자료를 잘라 내지 않습니다.
   - 색만으로 구분하지 않습니다. 축 단위, 오차 막대의 종류를 캡션에 씁니다.
4. **점검.** `python -m pa fig check 06_figures/out --min-dpi 600 --width-in <저널 본문 폭>`. 그림을 게재 크기로 렌더링해 직접 보고, 글자가 읽히는지 확인합니다.
5. **표.** 표도 스크립트로 만듭니다(Markdown 표 또는 LaTeX 표 본문 `07_manuscript/tex/gen/*.tex`). 세 줄 표, 의미 있는 이름, 각주에서 약어 정의.
6. 예산표의 상태 열을 채우고 `python -m pa gate S6`, `python -m pa mark S6 done`, 커밋합니다.

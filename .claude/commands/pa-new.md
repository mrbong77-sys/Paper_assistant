---
description: 새 논문 프로젝트를 만듭니다(폴더 체계, 설정, 로그).
argument-hint: <slug> [제목]
---

새 연구 프로젝트를 만듭니다. 인자: $ARGUMENTS

1. slug와 제목이 없으면 묻습니다. 함께 묻습니다(한 번에, 선택지와 권장안):
   - 분야 프로필: `python -m pa profiles`의 목록에서(권장: 연구 분야에 가장 가까운 것)
   - 원고 언어: en / ko
   - 대상 저널(정해졌으면)
   - 프로젝트를 둘 곳: 이 저장소의 `projects/`(git 제외, 권장) 또는 비공개 저장소(`PA_PROJECTS`)
2. 만듭니다:
   ```
   python -m pa new <slug> --title "<제목>" --field <프로필> --language <en|ko> --journal "<저널>"
   ```
3. `project.toml`의 `[people] owner`에 승인할 사람의 이름을 적습니다(이메일 등 신상 정보는 적지 않음).
4. `python -m pa --project <slug> status`를 보여 주고, 다음 단계가 `/pa-topic <slug>`임을 알립니다.
5. 프로젝트가 비공개 저장소에 있으면 첫 커밋을 합니다.

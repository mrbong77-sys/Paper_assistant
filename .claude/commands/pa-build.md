---
description: S9 — 원고를 DOCX 또는 LaTeX로 조립하고, 맹검판과 투고 묶음을 만들고, 사람이 승인하면 보낸 판을 동결합니다.
argument-hint: [slug] [docx|latex]
---

S9 조립과 투고. 인자: $ARGUMENTS.

1. 관문 S8이 열렸는지 확인합니다(`python -m pa gate S8`). 열리지 않았으면 막힌 이유를 알리고 멈춥니다.
2. **DOCX 원고(Markdown 원본):**
   ```
   python -m pa build docx                    # 07_manuscript/build/manuscript.docx (pandoc + citeproc)
   python -m pa build docx --blind            # 맹검판: <!-- identifying --> 구역 제거
   python -m pa build docx --pdf              # LibreOffice가 있으면 PDF도
   ```
   저널 Word 템플릿이 있으면 `07_manuscript/template.docx`로 두거나 `--reference-doc`으로 줍니다. 참고문헌 형식은 `--csl <style>.csl`(Zotero 스타일 저장소에서 저널 이름으로 찾음). pandoc이 없으면 내장 작성기로 만들어지지만 인용·그림은 빠집니다(경고).
3. **LaTeX 원고:** `07_manuscript/tex/main.tex`에 저널 클래스를 쓰고,
   ```
   python -m pa numbers macros                # numbers.tex
   python -m pa build latex                   # 오류·미해결 참조·인용이 있으면 실패
   python -m pa build latex --clean-copy      # revmarks.sty를 쓰는 수정본의 깨끗한 판
   python -m pa build package                 # 쓰인 파일만 zip → 빈 폴더에서 다시 조판 → submission/
   ```
4. **렌더링 확인.** PDF의 모든 쪽을 그림으로 렌더링해(`pdftoppm`) 표·그림 위치, 글꼴, 넘침을 직접 봅니다.
5. **묶음 점검(PK-01–PK-10).** 저널 체크리스트를 `submission/checklist.md`에 항목별로 채웁니다: 원고, 맹검판, 제목 페이지, 커버 레터, 그림 파일, 보충 자료, 선언문, 데이터·코드 링크(실제로 열리는지).
6. **커버 레터.** 기여와 저널 적합성, 미중복 투고 진술을 담은 초안을 `submission/cover_letter.md`에 씁니다.
7. **사람의 승인.** 묶음 목록과 렌더링 결과를 보여 승인을 청합니다. 사람이 승인하면 `python -m pa approve S9 --by <이름>`, 그리고 보낸 판을 동결합니다: `python -m pa round freeze`. **업로드는 사람이 합니다.**

# Local PDF Editor (Python)

**개인정보 유출 걱정 없는 100% 로컬 작동 PDF 편집기**

이 프로젝트는 외부 서버로 파일을 업로드하지 않고, 사용자의 기기 내에서만 모든 PDF 편집 작업을 수행하는 안드로이드 앱 개발을 목표로 합니다. 

---

## 핵심 기능 (Core Features)
현재 엔진 로직 구현 및 UI 연동 테스트 단계입니다.

* **🔄 페이지 회전 (Rotation):** 특정 페이지를 90도 단위로 자유롭게 회전.
* **✂️ 페이지 재배열 및 삭제 (Reorder & Delete):** 원하는 페이지 순서로 재구성하거나 불필요한 페이지 제거.
* **➕ 파일 병합 (Merge):** 여러 개의 PDF 파일을 하나로 통합.
* **🔒 로컬 처리 (100% Local):** 모든 프로세스가 오프라인으로 동작하여 강력한 보안성 제공.
* **추후 추가 예정**

---

## 🛠 기술 스택 (Tech Stack)

| 구분 | 기술 |
| :--- | :--- |
| **Language** | Python 3.11 |
| **PDF Engine** | PyMuPDF (fitz) |
| **UI Framework** | Flet (Flutter-based) |
| **VCS** | Git / GitHub |

---

## 시작하기 (Getting Started)

### 1. 가상환경 생성 및 활성화
```bash
python -m venv .venv
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# Mac/Linux
source .venv/bin/activate
```

### 2. 라이브러리 설치
```bash
pip install pymupdf flet
```

### 3. 앱 실행
```bash
python app.py
```

---

## 프로젝트 구조 (Project Structure)
* `main.py`: PDF 처리 핵심 엔진 로직 테스트 파일
* `app.py`: Flet 기반의 사용자 인터페이스 및 로직 통합 파일
* `.gitignore`: 가상환경 및 불필요한 캐시 파일 제외 설정

---

## 진행 상황 및 이슈
* [x] PyMuPDF 기반 핵심 엔진 개발 완료
* [x] Flet UI 기본 레이아웃 구성
* [ ] 안드로이드 빌드 환경 구성 및 최신 Flet 버전 최적화
* [ ] 드래그 앤 드롭 방식의 페이지 재배열 UI 구현 예정


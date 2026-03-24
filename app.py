import flet as ft
import fitz  # PyMuPDF
import os
import base64
import threading


# ──────────────────────────────────────────────
#  유틸
# ──────────────────────────────────────────────
ACCENT   = "#E53935"        # 빨간 포인트
BG       = "#F5F5F5"        # 전체 배경
CARD_BG  = "#FFFFFF"
TEXT     = "#212121"
SUBTEXT  = "#757575"
BORDER   = "#E0E0E0"

THUMB_W = 90
THUMB_H = 120


def render_thumbnail(doc, page_idx: int) -> str:
    """PDF 특정 페이지를 base64 PNG 문자열로 반환."""
    pg   = doc[page_idx]
    zoom = THUMB_W / pg.rect.width
    mat  = fitz.Matrix(zoom, zoom)
    pix  = pg.get_pixmap(matrix=mat, alpha=False)
    return base64.b64encode(pix.tobytes("png")).decode()


def placeholder_container():
    """썸네일 로딩 전 회색 플레이스홀더."""
    return ft.Container(
        content=ft.Icon(ft.Icons.IMAGE_OUTLINED, color="#BDBDBD", size=28),
        width=THUMB_W,
        height=THUMB_H,
        bgcolor="#F0F0F0",
        border_radius=6,
        alignment=ft.alignment.center,
        border=ft.border.all(1, BORDER),
    )
    
 
def loaded_thumb_container(b64: str):
    """base64 PNG를 감싼 컨테이너."""
    return ft.Image(
        content=ft.Image(
            src_base64=b64,
            width=THUMB_W,
            height=THUMB_H,
            fit="contain",
            border_radius=6,
        ),
        border=ft.border.all(1, BORDER),
        border_radius=6,
    )
    
    
# ──────────────────────────────────────────────
#  공통 UI 헬퍼
# ──────────────────────────────────────────────    
def card(content, padding=24, width=None):
    return ft.Container(
        content=content,
        bgcolor=CARD_BG,
        border_radius=16,
        padding=padding,
        width=width,
        shadow=ft.BoxShadow(blur_radius=12, color="#1A000000", offset=ft.Offset(0, 3)),
    )


def section_title(text):
    return ft.Text(text, size=13, weight="bold", color=SUBTEXT)


def file_button(label, color, on_click, icon=ft.Icons.UPLOAD_FILE):
    return ft.ElevatedButton(
        label, icon=icon, on_click=on_click,
        style=ft.ButtonStyle(bgcolor=color, color="#FFFFFF"),
    )
    

    
# ──────────────────────────────────────────────
#  페이지: 메인 홈
# ──────────────────────────────────────────────
def build_home(page: ft.Page, go):
    def feature_card(icon, title, desc, route, color):
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    ft.Icon(icon, color="#FFFFFF", size=28),
                    bgcolor=color,
                    border_radius=12,
                    padding=14,
                    width=56, height=56,
                ),
                ft.Container(height=14),
                ft.Text(title, size=16, weight="bold", color=TEXT),
                ft.Container(height=4),
                ft.Text(desc, size=12, color=SUBTEXT),
            ], spacing=0),
            bgcolor=CARD_BG,
            border_radius=16,
            padding=24,
            expand=True,
            shadow=ft.BoxShadow(blur_radius=12, color="#1A000000", offset=ft.Offset(0, 3)),
            on_click=lambda _: go(route),
            ink=True,
        )

    return ft.Column([
        ft.Container(height=32),
        ft.Row([
            ft.Container(
                ft.Icon(ft.Icons.PICTURE_AS_PDF, color=ACCENT, size=36),
                bgcolor="#FFF3F3",
                border_radius=12,
                padding=12,
            ),
            ft.Container(width=14),
            ft.Column([
                ft.Text("PDF 편집기", size=26, weight="bold", color=TEXT),
                ft.Text("간단하게 PDF를 편집하세요", size=13, color=SUBTEXT),
            ], spacing=2),
        ], vertical_alignment="center"),
        ft.Container(height=32),
        section_title("기능 선택"),
        ft.Container(height=12),
        ft.Row([
            feature_card(
                ft.Icons.ROTATE_RIGHT, "페이지 회전",
                "90도 단위로 원하는\n방향으로 회전",
                "rotate", "#E53935",
            ),
            feature_card(
                ft.Icons.REORDER, "페이지 재배열 / 삭제",
                "페이지 순서 변경 및\n불필요한 페이지 제거",
                "reorder", "#1E88E5",
            ),
            feature_card(
                ft.Icons.MERGE, "PDF 병합",
                "여러 PDF를 하나로\n통합, 순서도 지정 가능",
                "merge", "#43A047",
            ),
        ], spacing=16),
    ], spacing=0, scroll="auto")


# ──────────────────────────────────────────────
#  페이지: 회전
# ──────────────────────────────────────────────
def build_rotate(page: ft.Page, go):
    state = {"path": None, "name": None, "doc": None}
    cancel_flag = {"cancel": False, "gen": 0}  # gen: 세대 번호로 stale 업데이트 방지
    status = ft.Text("PDF 파일을 선택해주세요.", color=SUBTEXT, size=13)
    pages_col = ft.Column(spacing=12, scroll="auto")
    result_text = ft.Text("", color="#43A047", size=13, weight="bold")

    def build_page_list(doc):
        """플레이스홀더로 즉시 렌더링 후 지연 로딩 시작."""
        # 1) 이전 스레드 중단 표시
        cancel_flag["cancel"] = True
        cancel_flag["gen"]   += 1
        my_gen = cancel_flag["gen"]
        
        # 2) 플레이스홀더로 즉시 UI 구성
        pages_col.controls.clear()
        pages_col.controls.append(section_title(f"총 {len(doc)}페이지 — 회전할 방향 선택"))
        pages_col.controls.append(ft.Container(height=8))
 
        thumb_slots = []   # (slot_container, page_idx)
        for i in range(len(doc)):
            cur  = doc[i].rotation
            slot = placeholder_container()    # 회색 박스로 시작
            thumb_slots.append((slot, i))
 
            row = ft.Row([
                slot,
                ft.Container(width=16),
                ft.Column([
                    ft.Text(f"Page {i+1}", size=14, weight="bold", color=TEXT),
                    ft.Text(f"현재 회전: {cur}°", size=12, color=SUBTEXT),
                    ft.Container(height=8),
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.ROTATE_LEFT, tooltip="왼쪽 90°",
                            icon_color=ACCENT,
                            on_click=lambda _, idx=i: rotate_page(idx, -90),
                        ),
                        ft.Text("회전", size=12, color=SUBTEXT),
                        ft.IconButton(
                            icon=ft.Icons.ROTATE_RIGHT, tooltip="오른쪽 90°",
                            icon_color=ACCENT,
                            on_click=lambda _, idx=i: rotate_page(idx, 90),
                        ),
                    ], vertical_alignment="center", spacing=0),
                ], spacing=2),
            ], vertical_alignment="center")
 
            pages_col.controls.append(
                ft.Container(row, bgcolor=CARD_BG, border_radius=10,
                             padding=ft.padding.symmetric(10, 14),
                             border=ft.border.all(1, BORDER))
            )
 
        page.update()
        cancel_flag["cancel"] = False         # 새 로딩 시작
        
        def worker(gen):
            for slot, pg_idx in thumb_slots:
                if cancel_flag["cancel"] or cancel_flag["gen"] != gen:
                    break
                try:
                    b64 = render_thumbnail(doc, pg_idx)
                    # 슬롯이 아직 같은 세대일 때만 교체
                    if cancel_flag["gen"] == gen:
                        slot.content = ft.Image(
                            src_base64=b64,
                            width=THUMB_W, height=THUMB_H,
                            fit="contain", border_radius=6,
                        )
                        slot.bgcolor = None
                        slot.border  = ft.border.all(1, BORDER)
                        slot.update()   # ← page.update() 대신 slot만 업데이트
                except Exception:
                    pass
 
        threading.Thread(target=worker, args=(my_gen,), daemon=True).start()

    def rotate_page(idx, delta):
        doc = state["doc"]
        if not doc:
            return
        cur = doc[idx].rotation
        doc[idx].set_rotation((cur + delta) % 360)
        result_text.value = ""
        build_page_list(doc)

    def on_file_result(e):
        if e.files:
            f = e.files[0]
            state["path"] = f.path
            state["name"] = f.name
            state["doc"]  = fitz.open(f.path)
            status.value = f"📄 {f.name}"
            status.color = TEXT
            result_text.value = ""
            build_page_list(state["doc"])
        page.update()

    file_picker = ft.FilePicker()
    file_picker.on_result = on_file_result
    page.overlay.append(file_picker)
    page.update()

    def save(e):
        doc = state["doc"]
        if not doc:
            return
        base, ext = os.path.splitext(state["path"])
        out = base + "_rotated" + ext
        doc.save(out)
        result_text.value = f"✅ 저장 완료: {os.path.basename(out)}"
        result_text.color = "#43A047"
        page.update()

    return ft.Column([
        ft.Container(height=8),
        ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: go("home"), icon_color=TEXT),
            ft.Text("페이지 회전", size=22, weight="bold", color=TEXT),
        ], vertical_alignment="center"),
        ft.Container(height=20),
        card(ft.Column([
            section_title("파일 선택"),
            ft.Container(height=10),
            ft.Row([
                file_button("PDF 불러오기", ACCENT,
                            lambda _: file_picker.pick_files(allow_multiple=False, allowed_extensions=["pdf"])),
                ft.Container(width=12),
                status,
            ]),
        ])),
        ft.Container(height=16),
        card(pages_col),
        ft.Container(height=16),
        ft.Row([
            file_button("저장하기", "#212121", save, icon=ft.Icons.SAVE),
            ft.Container(width=12),
            result_text,
        ]),
        ft.Container(height=32),
    ], spacing=0, scroll="auto")


# ──────────────────────────────────────────────
#  페이지: 페이지 재배열 / 삭제
# ──────────────────────────────────────────────
def build_reorder(page: ft.Page, go):
    state = {"path": None, "name": None, "doc": None, "order": []}
    cancel_flag = {"cancel": False, "gen": 0}
    status    = ft.Text("PDF 파일을 선택해주세요.", color=SUBTEXT, size=13)
    pages_col = ft.Column(spacing=12, scroll="auto")
    result_text = ft.Text("", color="#43A047", size=13, weight="bold")

    def refresh_list():
        cancel_flag["cancel"] = True
        cancel_flag["gen"]   += 1
        my_gen = cancel_flag["gen"]
        
        doc   = state["doc"]
        order = state["order"]
        pages_col.controls.clear()
        
        if not doc or not order:
            page.update()
            return
        
        pages_col.controls.append(
            section_title(f"현재 순서 ({len(order)}페이지) — 이동·삭제 가능")
        )
        pages_col.controls.append(ft.Container(height=8))
        
        thumb_slots = []   # (slot, original_page_idx) 순서로 수집
        for pos, pg_idx in enumerate(order):
            slot = placeholder_container()
            thumb_slots.append((slot, pg_idx))

            def move_up(_, p=pos):
                if p > 0:
                    state["order"][p], state["order"][p-1] = state["order"][p-1], state["order"][p]
                    refresh_list()

            def move_down(_, p=pos):
                if p < len(state["order"]) - 1:
                    state["order"][p], state["order"][p+1] = state["order"][p+1], state["order"][p]
                    refresh_list()

            def delete(_, p=pos):
                state["order"].pop(p)
                refresh_list()

            row = ft.Row([
                slot,
                ft.Container(width=16),
                ft.Column([
                    ft.Text(f"원본 Page {pg_idx+1}", size=14, color=TEXT, weight="bold"),
                    ft.Text(f"→ {pos+1}번째로 배치", size=12, color=SUBTEXT),
                    ft.Container(height=8),
                    ft.Row([
                        ft.IconButton(ft.Icons.ARROW_UPWARD,   tooltip="위로", icon_color="#1E88E5", on_click=move_up),
                        ft.IconButton(ft.Icons.ARROW_DOWNWARD, tooltip="아래로", icon_color="#1E88E5", on_click=move_down),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE,  tooltip="삭제", icon_color=ACCENT, on_click=delete),
                    ], spacing=0),
                ], spacing=2),
            ], vertical_alignment="center")
            
            pages_col.controls.append(
                ft.Container(row, bgcolor=CARD_BG, border_radius=10,
                             padding=ft.padding.symmetric(10, 14),
                             border=ft.border.all(1, BORDER))
            )
        page.update()
        
        # 순서가 섞여도 올바른 페이지 썸네일을 로드
        cancel_flag["cancel"] = False
        
        def worker(gen):
            for slot, pg_idx in thumb_slots:
                if cancel_flag["cancel"] or cancel_flag["gen"] != gen:
                    break
                try:
                    b64 = render_thumbnail(doc, pg_idx)
                    if cancel_flag["gen"] == gen:
                        slot.content = ft.Image(
                            src_base64=b64,
                            width=THUMB_W, height=THUMB_H,
                            fit="contain", border_radius=6,
                        )
                        slot.bgcolor = None
                        slot.border = ft.border.all(1, BORDER)
                        slot.update()
                except Exception:
                    pass
                
        threading.Thread(target=worker, args=(my_gen,), daemon=True).start()

    def on_file_result(e):
        if e.files:
            f = e.files[0]
            doc = fitz.open(f.path)
            state["path"]  = f.path
            state["name"]  = f.name
            state["doc"]   = doc
            state["order"] = list(range(len(doc)))
            status.value = f"📄 {f.name}"
            status.color = TEXT
            result_text.value = ""
            refresh_list()
        page.update()

    file_picker = ft.FilePicker()
    file_picker.on_result = on_file_result
    page.overlay.append(file_picker)
    page.update()

    def save(e):
        if not state["path"] or not state["order"]:
            return
        src     = fitz.open(state["path"])
        out_doc = fitz.open()
        for idx in state["order"]:
            out_doc.insert_pdf(src, from_page=idx, to_page=idx)
        src.close()
        base, ext = os.path.splitext(state["path"])
        out_path = base + "_reordered" + ext
        out_doc.save(out_path)
        out_doc.close()
        result_text.value = f"✅ 저장 완료: {os.path.basename(out_path)}"
        result_text.color = "#43A047"
        page.update()

    return ft.Column([
        ft.Container(height=8),
        ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: go("home"), icon_color=TEXT),
            ft.Text("페이지 재배열 / 삭제", size=22, weight="bold", color=TEXT),
        ], vertical_alignment="center"),
        ft.Container(height=20),
        card(ft.Column([
            section_title("파일 선택"),
            ft.Container(height=10),
            ft.Row([
                file_button("PDF 불러오기", "#1E88E5",
                            lambda _: file_picker.pick_files(allow_multiple=False,
                                                             allowed_extensions=["pdf"])),
                ft.Container(width=12),
                status,
            ]),
        ])),
        ft.Container(height=16),
        card(pages_col),
        ft.Container(height=16),
        ft.Row([
            file_button("저장하기", "#212121", save, icon=ft.Icons.SAVE),
            ft.Container(width=12),
            result_text,
        ]),
        ft.Container(height=32),
    ], spacing=0, scroll="auto")


# ──────────────────────────────────────────────
#  페이지: PDF 병합
# ──────────────────────────────────────────────
def build_merge(page: ft.Page, go):
    files_list  = []   # [{"path": ..., "name": ..., "thumb_b64": ...}]
    files_col   = ft.Column(spacing=12, scroll="auto")
    result_text = ft.Text("", color="#43A047", size=13, weight="bold")

    def refresh_list():
        files_col.controls.clear()
        if not files_list:
            files_col.controls.append(
                ft.Text("아직 파일이 없어요.", color=SUBTEXT, size=13)
            )
            page.update()
            return
        
        files_col.controls.append(
            section_title(f"선택된 파일 ({len(files_list)}개) — 순서 변경 가능")
        )
        
        files_col.controls.append(ft.Container(height=8))
        
        for i, f in enumerate(files_list):
            def move_up(_, idx=i):
                if idx > 0:
                    files_list[idx], files_list[idx-1] = files_list[idx-1], files_list[idx]
                    refresh_list()

            def move_down(_, idx=i):
                if idx < len(files_list) - 1:
                    files_list[idx], files_list[idx+1] = files_list[idx+1], files_list[idx]
                    refresh_list()

            def remove(_, idx=i):
                files_list.pop(idx)
                refresh_list()

            row = ft.Row([
                ft.Container(
                    ft.Text(f"{i+1}", size=13, color="#FFFFFF", weight="bold"),
                    bgcolor="#43A047", border_radius=8,
                    width=28, height=28,
                    alignment=ft.alignment.center,
                ),
                ft.Container(width=12),
                f["slot"],          # 썸네일 슬롯 (이미 로딩됐거나 플레이스홀더)
                ft.Container(width=16),
                ft.Column([
                    ft.Text(f["name"], size=13, color=TEXT, weight="bold"),
                    ft.Text("1페이지 미리보기", size=11, color=SUBTEXT),
                    ft.Container(height=8),
                    ft.Row([
                        ft.IconButton(ft.Icons.ARROW_UPWARD,   tooltip="위로", icon_color="#43A047", on_click=move_up),
                        ft.IconButton(ft.Icons.ARROW_DOWNWARD, tooltip="아래로", icon_color="#43A047", on_click=move_down),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE,  tooltip="제거", icon_color=ACCENT, on_click=remove),
                    ], spacing=0),
                ], spacing=2, expand=True),                
            ], vertical_alignment="center")
            
            files_col.controls.append(
                ft.Container(row, bgcolor=CARD_BG, border_radius=10,
                             padding=ft.padding.symmetric(10, 14),
                             border=ft.border.all(1, BORDER))
            )
            
        page.update()

    def load_thumb_async(slot, doc):
        """병합: 첫 페이지만 비동기 로드. page.update() 대신 slot.update()."""
        def worker():
            try:
                b64 = render_thumbnail(doc, 0)
                doc.close()
                slot.content = ft.Image(
                    src_base64=b64,
                    width=THUMB_W, height=THUMB_H,
                    fit="contain", border_radius=6,
                )
                slot.bgcolor = None
                slot.border  = ft.border.all(1, BORDER)
                slot.update()
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()
        
    def on_file_result(e):
        if e.files:
            new_slots = []
            for f in e.files:
                # 중복 방지
                if not any(x["path"] == f.path for x in files_list):
                    slot = placeholder_container()
                    files_list.append({"path": f.path, "name": f.name, "slot": slot})
                    new_slots.append((slot, f.path))
            result_text.value = ""
            refresh_list()  # page.update() 포함 — slot 등록 완료
            # 등록 완료 후 비동기 로드
            for slot, path in new_slots:
                load_thumb_async(slot, fitz.open(path))
        page.update()

    file_picker = ft.FilePicker()
    file_picker.on_result = on_file_result
    page.overlay.append(file_picker)
    page.update()

    def save(e):
        if len(files_list) < 2:
            result_text.value = "⚠️ 최소 2개 파일이 필요합니다."
            result_text.color = "#FB8C00"
            page.update()
            return
        out_doc = fitz.open()
        for f in files_list:
            src = fitz.open(f["path"])
            out_doc.insert_pdf(src)
            src.close()
        first_dir  = os.path.dirname(files_list[0]["path"])
        out_path   = os.path.join(first_dir, "merged_output.pdf")
        out_doc.save(out_path)
        out_doc.close()
        result_text.value = f"✅ 저장 완료: {out_path}"
        result_text.color = "#43A047"
        page.update()

    return ft.Column([
        ft.Container(height=8),
        ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: go("home"), icon_color=TEXT),
            ft.Text("PDF 병합", size=22, weight="bold", color=TEXT),
        ], vertical_alignment="center"),
        ft.Container(height=20),
        card(ft.Column([
            section_title("파일 추가"),
            ft.Container(height=10),
            file_button("PDF 파일 추가 (복수 선택 가능)", "#43A047",
                        lambda _: file_picker.pick_files(allow_multiple=True,
                                                         allowed_extensions=["pdf"]),
                        icon=ft.Icons.ADD),
        ])),
        ft.Container(height=16),
        card(files_col),
        ft.Container(height=16),
        ft.Row([
            file_button("병합 후 저장", "#212121", save, icon=ft.Icons.MERGE),
            ft.Container(width=12),
            result_text,
        ]),
        ft.Container(height=32),
    ], spacing=0, scroll="auto")


# ──────────────────────────────────────────────
#  라우터 + 앱 진입점
# ──────────────────────────────────────────────
def main(page: ft.Page):
    page.title         = "PDF 편집기"
    page.bgcolor       = BG
    page.padding       = ft.padding.symmetric(horizontal=40, vertical=20)
    page.window.width  = 860
    page.window.height = 720

    content = ft.Column(expand=True, scroll="auto")

    def go(route):
        # 이전 overlay 정리 (FilePicker 중복 방지)
        page.overlay.clear()
        content.controls.clear()
        if route == "home":
            content.controls.append(build_home(page, go))
        elif route == "rotate":
            content.controls.append(build_rotate(page, go))
        elif route == "reorder":
            content.controls.append(build_reorder(page, go))
        elif route == "merge":
            content.controls.append(build_merge(page, go))
        page.update()

    page.add(content)
    go("home")


ft.app(target=main)
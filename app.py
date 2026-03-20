import flet as ft
import fitz  # PyMuPDF
import os
import base64


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
 
 
def thumb_image(b64: str):
    return ft.Image(
        src_base64=b64,
        width=THUMB_W,
        height=THUMB_H,
        fit="contain",
        border_radius=6,
    )
    
    
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


def divider():
    return ft.Divider(height=1, color=BORDER)


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
    selected_file = {"path": None, "name": None, "doc": None}
    status = ft.Text("PDF 파일을 선택해주세요.", color=SUBTEXT, size=13)
    pages_col = ft.Column(spacing=8, scroll="auto")
    result_text = ft.Text("", color="#43A047", size=13, weight="bold")

    def refresh_page_list():
        pages_col.controls.clear()
        doc = selected_file["doc"]
        if not doc:
            page.update()
            return
        pages_col.controls.append(section_title(f"총 {len(doc)}페이지 — 회전할 방향 선택"))
        pages_col.controls.append(ft.Container(height=8))
        for i in range(len(doc)):
            cur = doc[i].rotation
            b64 = render_thumbnail(doc, i)
            
            row = ft.Row([
                ft.Container(
                    thumb_image(b64),
                    border = ft.border.all(1, BORDER),
                    border_radius=6,
                ),
                ft.Container(width=16),
                ft.Column([
                    ft.Text(f"Page {i+1}", size=14, color=TEXT, weight="bold"),
                    ft.Text(f"현재 회전: {cur}°", size=12, color=SUBTEXT),
                    ft.Container(height=8),
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.ROTATE_LEFT,
                            tooltip="왼쪽 90°",
                            icon_color=ACCENT,
                            on_click=lambda _, idx=i: rotate_page(idx, -90),
                        ),
                        ft.Text("회전", size=12, color=SUBTEXT),
                        ft.IconButton(
                            icon=ft.Icons.ROTATE_RIGHT,
                            tooltip="오른쪽 90°",
                            icon_color=ACCENT,
                            on_click=lambda _, idx=i: rotate_page(idx, 90),
                        ),
                    ], vertical_alignment="center", spacing=0),
                ], spacing=2),
            ], vertical_alignment="center")
            
            pages_col.controls.append(
                ft.Container(row, bgcolor=CARD_BG, border_radius=10,
                             padding=ft.padding.symmetric(8, 12),
                             border=ft.border.all(1, BORDER))
            )
        page.update()

    def rotate_page(idx, delta):
        doc = selected_file["doc"]
        cur = doc[idx].rotation
        doc[idx].set_rotation((cur + delta) % 360)
        result_text.value = ""
        refresh_page_list()

    def on_file_result(e):
        if e.files:
            f = e.files[0]
            selected_file["path"] = f.path
            selected_file["name"] = f.name
            selected_file["doc"]  = fitz.open(f.path)
            status.value = f"📄 {f.name}"
            status.color = TEXT
            result_text.value = ""
            refresh_page_list()
        page.update()

    file_picker = ft.FilePicker()
    file_picker.on_result = on_file_result
    page.overlay.append(file_picker)
    page.update()

    def save(e):
        doc = selected_file["doc"]
        if not doc:
            return
        base, ext = os.path.splitext(selected_file["path"])
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
                ft.ElevatedButton(
                    "PDF 불러오기",
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=lambda _: file_picker.pick_files(
                        allow_multiple=False, allowed_extensions=["pdf"]
                    ),
                    style=ft.ButtonStyle(bgcolor=ACCENT, color="#FFFFFF"),
                ),
                ft.Container(width=12),
                status,
            ]),
        ])),
        ft.Container(height=16),
        card(pages_col),
        ft.Container(height=16),
        ft.Row([
            ft.ElevatedButton(
                "저장하기",
                icon=ft.Icons.SAVE,
                on_click=save,
                style=ft.ButtonStyle(bgcolor="#212121", color="#FFFFFF"),
            ),
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
    status    = ft.Text("PDF 파일을 선택해주세요.", color=SUBTEXT, size=13)
    pages_col = ft.Column(spacing=12, scroll="auto")
    result_text = ft.Text("", color="#43A047", size=13, weight="bold")

    def refresh_list():
        pages_col.controls.clear()
        doc   = state["doc"]
        order = state["order"]
        if not doc or not order:
            page.update()
            return
        pages_col.controls.append(
            section_title(f"현재 순서 ({len(order)}페이지) — 이동·삭제 가능")
        )
        pages_col.controls.append(ft.Container(height=8))
        for pos, pg_idx in enumerate(order):
            b64 = render_thumbnail(doc, pg_idx)

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
                ft.Container(
                    thumb_image(b64),
                    border=ft.border.all(1, BORDER),
                    border_radius=6,
                ),
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
                ft.ElevatedButton(
                    "PDF 불러오기",
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=lambda _: file_picker.pick_files(
                        allow_multiple=False, allowed_extensions=["pdf"]
                    ),
                    style=ft.ButtonStyle(bgcolor="#1E88E5", color="#FFFFFF"),
                ),
                ft.Container(width=12),
                status,
            ]),
        ])),
        ft.Container(height=16),
        card(pages_col),
        ft.Container(height=16),
        ft.Row([
            ft.ElevatedButton(
                "저장하기",
                icon=ft.Icons.SAVE,
                on_click=save,
                style=ft.ButtonStyle(bgcolor="#212121", color="#FFFFFF"),
            ),
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
                ft.Container(
                    thumb_image(f["thumb_b64"]),
                    border=ft.border.all(1, BORDER),
                    border_radius=6,
                ),
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

    def on_file_result(e):
        if e.files:
            for f in e.files:
                # 중복 방지
                if not any(x["path"] == f.path for x in files_list):
                    doc = fitz.open(f.path)
                    b64 = render_thumbnail(doc, 0)
                    doc.close()
                    files_list.append({"path": f.path, "name": f.name, "thumb_b64": b64})
            result_text.value = ""
            refresh_list()
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
            ft.ElevatedButton(
                "PDF 파일 추가 (복수 선택 가능)",
                icon=ft.Icons.ADD,
                on_click=lambda _: file_picker.pick_files(
                    allow_multiple=True, allowed_extensions=["pdf"]
                ),
                style=ft.ButtonStyle(bgcolor="#43A047", color="#FFFFFF"),
            ),
        ])),
        ft.Container(height=16),
        card(files_col),
        ft.Container(height=16),
        ft.Row([
            ft.ElevatedButton(
                "병합 후 저장",
                icon=ft.Icons.MERGE,
                on_click=save,
                style=ft.ButtonStyle(bgcolor="#212121", color="#FFFFFF"),
            ),
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
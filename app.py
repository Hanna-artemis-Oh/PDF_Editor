import flet as ft
import fitz  # PyMuPDF

def main(page: ft.Page):
    page.title = "PDF Editor"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"

    status_text = ft.Text("수정할 PDF 파일을 선택해주세요.", color="grey")

    def handle_file_result(e):
        if e.files:
            try:
                file_path = e.files[0].path
                status_text.value = f"선택됨: {e.files[0].name}\n편집 중..."
                page.update()

                doc = fitz.open(file_path)
                if len(doc) > 0:
                    doc[0].set_rotation(90)

                output_path = file_path.replace(".pdf", "_rotated.pdf")
                doc.save(output_path)
                doc.close()

                status_text.value = f"✅ 성공! 파일 생성됨:\n{output_path}"
                status_text.color = "blue"
            except Exception as ex:
                status_text.value = f"❌ 에러: {str(ex)}"
                status_text.color = "red"
        else:
            status_text.value = "파일 선택이 취소되었습니다."
            status_text.color = "grey"
        page.update()

    # ✅ 생성자에 on_result 넣지 않고, 속성으로 따로 할당
    file_picker = ft.FilePicker()
    file_picker.on_result = handle_file_result

    page.overlay.append(file_picker)
    page.update()

    page.add(
        ft.Column(
            [
                ft.Icon(ft.Icons.PICTURE_AS_PDF, color="red", size=80),  # ✅ ft.Icons 대문자
                ft.Text("PDF 로컬 편집기", size=25, weight="bold"),
                status_text,
                ft.ElevatedButton(
                    text="PDF 파일 불러오기",
                    icon=ft.Icons.UPLOAD_FILE,  # ✅ ft.Icons 대문자
                    on_click=lambda _: file_picker.pick_files(
                        allow_multiple=False,
                        allowed_extensions=["pdf"]
                    ),
                )
            ],
            horizontal_alignment="center",
        )
    )

ft.app(target=main)
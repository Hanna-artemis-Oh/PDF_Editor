import fitz  # PyMuPDF 라이브러리

def pdf_processor():
    # 1. 파일 불러오기
    input_file = "test.pdf" 
    doc = fitz.open(input_file)
    print(f"문서 오픈 성공: {input_file} (총 {len(doc)}페이지)")

    # --- [기능 1: 로테이션] ---
    # 1번째 페이지(인덱스 0)를 90도 회전
    doc[0].set_rotation(90)
    print("1페이지를 90도 회전시켰습니다.")

    # --- [기능 2: 페이지 재배열 및 삭제] ---
    # 예: 1페이지와 3페이지(인덱스 0, 2)만 남기고 순서를 바꿈
    # 주의: 실제 파일에 페이지가 3장 이상 있어야 에러가 안 납니다!
    if len(doc) >= 3:
        doc.select([2, 0]) 
        print("페이지 순서를 [3번, 1번]으로 바꾸고 나머지는 삭제했습니다.")

    # --- [기능 3: 여러 파일 합치기] ---
    # 테스트를 위해 자기 자신을 한 번 더 뒤에 붙여볼게요.
    new_doc = fitz.open(input_file)
    doc.insert_pdf(new_doc)
    print("파일 합치기 완료.")

    # 최종 결과 저장
    output_file = "result_fixed.pdf"
    doc.save(output_file)
    doc.close()
    print(f"최종 파일 저장 완료: {output_file}")

if __name__ == "__main__":
    pdf_processor()
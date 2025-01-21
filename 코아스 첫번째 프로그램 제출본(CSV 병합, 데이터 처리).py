#코아스 첫번째 프로그램 제출본(CSV 병합, 데이터 처리)
import pandas as pd
from tkinter import Tk, Label, Button, messagebox, StringVar, OptionMenu, BooleanVar, Checkbutton
from tkinter import ttk  # ProgressBar를 사용하기 위해 추가
import chardet
import requests

# ─────────────────────────────────────────────────────────
# 1) 네이버 클라우드 플랫폼에서 발급받은 Client ID / Secret
NAVER_CLIENT_ID = ""     # 네이버 지도 API Client ID
NAVER_CLIENT_SECRET = ""  # 네이버 지도 API Client Secret
GPT_API_KEY = ""  # ChatGPT API Key
# ─────────────────────────────────────────────────────────

# CSV 파일 경로 설정
SAFETY_FILE = r"C:\Users\dghlu\OneDrive\바탕 화면\폴더버거\대학 파일\대회 겸 포폴\코아스 건축디자인 관련 공모전\쓸꺼\국토안전관리원_공공건축물 에너지 소비량_20240331.csv"
MERGED_FILE = r"C:\Users\dghlu\OneDrive\바탕 화면\폴더버거\대학 파일\대회 겸 포폴\코아스 건축디자인 관련 공모전\쓸꺼\A~H합병.csv"
YANGSAN_FILE = r"C:\Users\dghlu\OneDrive\바탕 화면\폴더버거\대학 파일\대회 겸 포폴\코아스 건축디자인 관련 공모전\쓸꺼\경상남도 양산시_공동주택(아파트) 연한별 현황_20210809.csv"

# 파일 인코딩 감지 함수
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        rawdata = f.read()
    result = chardet.detect(rawdata)
    return result['encoding']

# CSV 읽기 함수
def read_csv_with_debug(file_path):
    try:
        encoding = detect_encoding(file_path)
        return pd.read_csv(file_path, encoding=encoding)
    except Exception as e:
        messagebox.showerror("오류", f"{file_path} 파일을 읽는 중 오류 발생:\n{str(e)}")
        raise

# 데이터 처리 함수
def process_data(selected_sido, selected_sigungu, save_csv, progress_bar):
    try:
        # 지역 필터링 확인
        if selected_sido != "경상남도" or selected_sigungu != "양산시":
            messagebox.showerror("오류", "현재는 경상남도 양산시만 지원됩니다.")
            return

        # 진행바 초기화
        progress_bar['value'] = 0
        progress_bar.update()

        # 데이터 로드
        safety_data = read_csv_with_debug(SAFETY_FILE)
        yangsan_data = read_csv_with_debug(YANGSAN_FILE)

        # 총 행 개수 파악
        total_rows = len(safety_data) + len(yangsan_data)
        processed_rows = 0

        # 결과 데이터를 저장할 DataFrame
        result = pd.DataFrame(columns=["지역", "건물명", "준공년도", "20년 이상 여부", "에너지효율등급"])

        # 국토안전관리원 데이터 처리
        for _, row in safety_data.iterrows():
            소재지 = str(row.get("소재지", ""))
            건물명 = str(row.get("건물명", "정보 없음"))
            준공년도 = str(row.get("사용승인연도", "정보 없음"))[:4]

            if "양산" not in 소재지:
                continue

            over_20 = "O" if 준공년도.isdigit() and (2023 - int(준공년도) >= 20) else "X"
            new_row = pd.DataFrame([{
                "지역": 소재지,
                "건물명": 건물명,
                "준공년도": 준공년도,
                "20년 이상 여부": over_20,
                "에너지효율등급": "정보 없음"
            }])
            result = pd.concat([result, new_row], ignore_index=True)

            # 진행바 업데이트
            processed_rows += 1
            progress_bar['value'] = (processed_rows / total_rows) * 100
            progress_bar.update()

        # 양산시 공동주택 데이터 처리
        for _, row in yangsan_data.iterrows():
            준공년도 = str(row.get("준공일", "정보 없음"))[:4]
            아파트명 = str(row.get("아파트명", "정보 없음"))

            over_20 = "O" if 준공년도.isdigit() and (2023 - int(준공년도) >= 20) else "X"

            new_row = pd.DataFrame([{
                "지역": "양산시",
                "건물명": 아파트명,
                "준공년도": 준공년도,
                "20년 이상 여부": over_20,
                "에너지효율등급": "정보 없음"
            }])
            result = pd.concat([result, new_row], ignore_index=True)

            # 진행바 업데이트
            processed_rows += 1
            progress_bar['value'] = (processed_rows / total_rows) * 100
            progress_bar.update()

        # 데이터가 비어있는 경우 처리
        if result.empty:
            messagebox.showinfo("완료", "필터링된 데이터가 없습니다.")
            return

        # 파일 저장 옵션 체크
        if save_csv:
            output_file = "processed_data.csv"
            result.to_csv(output_file, index=False, encoding="utf-8-sig")
            messagebox.showinfo("완료", f"데이터 가공 완료\n총 {len(result)}건이 처리되었습니다.\n결과 파일: {output_file}")
        else:
            messagebox.showinfo("완료", f"데이터 가공 완료\n총 {len(result)}건이 처리되었습니다. (CSV 저장 안 함)")

    except Exception as e:
        messagebox.showerror("오류", f"데이터 처리 중 오류 발생:\n{str(e)}")

# Tkinter GUI 설정
def main():
    root = Tk()
    root.title("건물 데이터 처리 프로그램")

    Label(root, text="건물 데이터 처리 프로그램", font=("Arial", 16)).pack(pady=10)

    # 지역 선택 변수
    selected_sido = StringVar(root)
    selected_sigungu = StringVar(root)

    # 초기값 설정
    selected_sido.set("경상남도")
    selected_sigungu.set("양산시")

    # 시/도 선택
    Label(root, text="시/도", font=("Arial", 12)).pack()
    sido_menu = OptionMenu(root, selected_sido, "경상남도")
    sido_menu.pack()

    # 시/군/구 선택
    Label(root, text="시/군/구", font=("Arial", 12)).pack()
    sigungu_menu = OptionMenu(root, selected_sigungu, "양산시")
    sigungu_menu.pack()

    # CSV 저장 여부 체크박스
    save_csv_var = BooleanVar()
    save_csv_var.set(True)
    Checkbutton(root, text="CSV 파일 저장", variable=save_csv_var).pack()

    # 진행바 추가
    progress_bar = ttk.Progressbar(root, length=300, mode='determinate')
    progress_bar.pack(pady=10)

    # 데이터 처리 버튼
    def on_process_button():
        messagebox.showinfo("알림", "데이터 처리 중입니다. 잠시만 기다려주세요.")
        process_data(
            selected_sido.get(),
            selected_sigungu.get(),
            save_csv_var.get(),
            progress_bar
        )

    Button(root, text="데이터 처리 시작", command=on_process_button, font=("Arial", 12)).pack(pady=10)

    root.geometry("500x400")
    root.mainloop()

if __name__ == "__main__":
    main()

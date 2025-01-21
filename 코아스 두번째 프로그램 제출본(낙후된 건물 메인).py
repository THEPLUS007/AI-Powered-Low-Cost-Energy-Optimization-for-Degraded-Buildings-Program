import pandas as pd
from tkinter import Tk, Toplevel, Label, Button, filedialog, messagebox, ttk, Scrollbar, VERTICAL, HORIZONTAL
import requests
import chardet  # 파일 인코딩 감지에 사용

# API 키 설정
NAVER_CLIENT_ID = ""
NAVER_CLIENT_SECRET = ""
GPT_API_KEY = ""

# 파일 인코딩 감지 함수
def detect_encoding(file_path):
    try:
        with open(file_path, 'rb') as f:
            rawdata = f.read()
        result = chardet.detect(rawdata)
        return result['encoding']
    except Exception as e:
        messagebox.showerror("오류", f"파일 인코딩 감지 중 오류 발생: {str(e)}")
        raise

# CSV 읽기 함수
def read_csv_with_debug(file_path):
    try:
        encoding = detect_encoding(file_path)
        print(f"DEBUG: 감지된 인코딩 - {encoding}")
        df = pd.read_csv(file_path, encoding=encoding)
        print(f"DEBUG: 데이터 로드 성공. 행 수: {len(df)}")
        return df
    except Exception as e:
        print(f"DEBUG: CSV 읽기 오류 - {str(e)}")
        messagebox.showerror("오류", f"{file_path} 파일을 읽는 중 오류 발생: {str(e)}")
        raise

# 지도 API 호출 (지오코딩으로 좌표 가져오기)
def get_coordinates(address):
    try:
        url = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
        headers = {
            "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
            "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET,
        }
        params = {"query": address}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('addresses'):
                x = data['addresses'][0]['x']
                y = data['addresses'][0]['y']
                return x, y
    except Exception as e:
        print(f"지도 API 호출 중 오류: {e}")
    return None, None

# GPT API 호출
def get_gpt_solution(building_name, year, efficiency):
    try:
        prompt = f"""
        건물명: {building_name}
        준공년도: {year}
        에너지 효율등급: {efficiency}

        위 건물이 낙후된 에너지 효율을 개선하기 위한 저비용 솔루션을 제시해주세요.
        """
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GPT_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            print(f"GPT API 오류: {response.status_code}, {response.text}")
            return f"GPT API 호출 오류: {response.status_code}, {response.text}"
    except Exception as e:
        print(f"GPT API 호출 중 오류: {e}")
        return "솔루션 생성 중 오류 발생"

# 새로운 창 생성 (지도 + 좌표 표시 + GPT 솔루션)
def show_building_details(building_info):
    top = Toplevel()
    top.title("건물 상세 정보")
    top.geometry("600x600")

    try:
        Label(top, text=f"건물명: {building_info['건물명']}", font=("Arial", 14)).pack(pady=10)
        Label(top, text=f"주소: {building_info['지역']}", font=("Arial", 12)).pack(pady=5)
        Label(top, text=f"준공년도: {building_info['준공년도']}", font=("Arial", 12)).pack(pady=5)
        Label(top, text=f"에너지효율등급: {building_info['에너지효율등급']}", font=("Arial", 12)).pack(pady=5)

        x, y = get_coordinates(building_info['지역'])
        if x and y:
            Label(top, text=f"위도: {y}, 경도: {x}", font=("Arial", 12), fg="blue").pack(pady=10)
        else:
            Label(top, text="좌표 데이터를 가져오지 못했습니다.", font=("Arial", 10), fg="red").pack(pady=5)

        solution = get_gpt_solution(
            building_name=building_info['건물명'],
            year=building_info['준공년도'],
            efficiency=building_info['에너지효율등급']
        )
        Label(top, text="GPT 솔루션:", font=("Arial", 12)).pack(pady=10)
        Label(top, text=solution, font=("Arial", 10), wraplength=550, justify="left").pack(pady=10)

    except Exception as e:
        Label(top, text=f"오류 발생: {str(e)}", font=("Arial", 10), fg="red").pack(pady=5)

# 테이블 표시 및 클릭 이벤트
def show_building_table(data):
    root = Tk()
    root.title("건물 목록")
    root.geometry("900x700")

    Label(root, text="건물 목록", font=("Arial", 16)).pack(pady=10)

    frame = ttk.Frame(root)
    frame.pack(fill="both", expand=True)
    tree = ttk.Treeview(frame, columns=list(data.columns), show="headings", height=20)

    vsb = ttk.Scrollbar(frame, orient=VERTICAL, command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient=HORIZONTAL, command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")

    for col in data.columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=120)

    for _, row in data.iterrows():
        tree.insert("", "end", values=row.tolist())

    tree.pack(fill="both", expand=True)

    def on_row_select(event):
        item = tree.selection()[0]
        selected_row = tree.item(item, "values")
        building_info = dict(zip(data.columns, selected_row))
        show_building_details(building_info)

    tree.bind("<Double-1>", on_row_select)
    root.mainloop()

def upload_and_process_csv():
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
    if not file_path:
        return

    try:
        data = read_csv_with_debug(file_path)
        print(f"DEBUG: 데이터 로드 완료. 컬럼: {data.columns.tolist()}")
        show_building_table(data)
    except Exception as e:
        print(f"DEBUG: CSV 처리 오류 - {str(e)}")
        messagebox.showerror("오류", f"CSV 파일 처리 중 오류 발생: {str(e)}")

def main():
    root = Tk()
    root.title("건물 데이터 관리 프로그램")
    root.geometry("400x200")

    Label(root, text="건물 데이터 관리 프로그램", font=("Arial", 16)).pack(pady=20)
    Button(root, text="CSV 파일 업로드", command=upload_and_process_csv, font=("Arial", 12)).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()

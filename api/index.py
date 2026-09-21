import os
import io
from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__, template_folder='../templates')

@app.route('/', methods=['GET', 'POST'])
def index():
    filters_data = []
    selected_filters = {}
    error_msg = None
    data_html = None

    if request.method == 'POST':
        try:
            if 'file' in request.files and request.files['file'].filename != '':
                file = request.files['file']
                file_bytes = file.read()

                if file_bytes:
                    df = None
                    # ลองอ่านแบบ TIS-620 (ภาษาไทย) และ UTF-8 ตรงๆ เพื่อความเร็ว
                    for enc in ['tis-620', 'utf-8', 'utf-8-sig', 'cp874']:
                        try:
                            stream = io.BytesIO(file_bytes)
                            df = pd.read_csv(stream, encoding=enc, sep=None, engine='python', on_bad_lines='skip')
                            if df is not None and not df.empty and len(df.columns) > 1:
                                break
                        except Exception:
                            continue

                    if df is not None and not df.empty:
                        # 1. ดึงค่าตัวกรอง
                        for key in request.form:
                            if key.startswith('filter_'):
                                c_name = key.replace('filter_', '')
                                val = request.form.get(key)
                                if val and val != 'ALL':
                                    selected_filters[c_name] = val

                        # 2. ทำตัวเลือก Filter แบบเบาที่สุด
                        for col in df.columns:
                            col_str = str(col)
                            try:
                                unique_vals = df[col].dropna().unique().tolist()
                                sorted_vals = sorted([str(v) for v in unique_vals])
                            except Exception:
                                sorted_vals = [str(v) for v in df[col].dropna().unique().tolist()]

                            filters_data.append({
                                'column': col_str,
                                'values': sorted_vals
                            })

                        # 3. กรองข้อมูล
                        filtered_df = df.copy()
                        for col_name, selected_val in selected_filters.items():
                            if col_name in filtered_df.columns:
                                filtered_df[col_name] = filtered_df[col_name].astype(str).str.strip()
                                filtered_df = filtered_df[filtered_df[col_name] == str(selected_val).strip()]

                        # 4. แสดงผลตาราง (แสดงสูงสุด 500 แถวเพื่อไม่ให้หน้าเว็บหน่วง)
                        data_html = filtered_df.head(500).to_html(classes='table table-striped table-hover', index=False)
                    else:
                        error_msg = "ไม่สามารถอ่านโครงสร้างข้อมูลในไฟล์ได้ กรุณาตรวจสอบไฟล์อีกครั้ง"
                else:
                    error_msg = "ไฟล์ที่อัปโหลดไม่มีข้อมูล"
        except Exception as e:
            error_msg = f"เกิดข้อผิดพลาด: {str(e)}"

    return render_template('index.html', 
                           data_html=data_html, 
                           filters_data=filters_data, 
                           selected_filters=selected_filters, 
                           error_msg=error_msg)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
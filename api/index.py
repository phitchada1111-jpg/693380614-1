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
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            try:
                file_bytes = file.read()
                if file_bytes:
                    encodings = ['utf-8', 'tis-620', 'cp874', 'utf-8-sig', 'latin1']
                    separators = ['\t', ',', ';']
                    df = None

                    for enc in encodings:
                        for sep in separators:
                            try:
                                stream = io.BytesIO(file_bytes)
                                temp_df = pd.read_csv(stream, encoding=enc, sep=sep, on_bad_lines='skip')
                                if temp_df is not None and not temp_df.empty and len(temp_df.columns) > 1:
                                    df = temp_df
                                    break
                            except Exception:
                                continue
                        if df is not None:
                            break

                    if df is not None and not df.empty:
                        # 1. ดึงค่า Filter จากฟอร์ม
                        for key in request.form:
                            if key.startswith('filter_'):
                                c_name = key.replace('filter_', '')
                                val = request.form.get(key)
                                if val and val != 'ALL':
                                    selected_filters[c_name] = val

                        # 2. สร้างรายการตัวเลือก Filter
                        for col in df.columns:
                            col_str = str(col)
                            try:
                                raw_vals = df[col].dropna().unique().tolist()
                                sorted_vals = sorted([str(v) for v in raw_vals])
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

                        # 4. แปลงเป็นตาราง HTML
                        data_html = filtered_df.to_html(classes='table table-striped table-hover', index=False)
                    else:
                        error_msg = "ไม่สามารถอ่านโครงสร้างคอลัมน์ในไฟล์ได้ กรุณาตรวจสอบไฟล์อีกครั้ง"
                else:
                    error_msg = "ไฟล์ที่อัปโหลดไม่มีข้อมูล"

            except Exception as e:
                error_msg = f"เกิดข้อผิดพลาดในการประมวลผลไฟล์: {str(e)}"

    return render_template('index.html', 
                           data_html=data_html, 
                           filters_data=filters_data, 
                           selected_filters=selected_filters, 
                           error_msg=error_msg)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
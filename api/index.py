import os
import io
from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__, template_folder='../templates')

def load_dataframe_from_file(file_storage):
    try:
        content = file_storage.read()
        encodings = ['utf-8', 'tis-620', 'cp874', 'utf-8-sig', 'latin1']
        separators = [None, '\t', ',', ';']
        
        for enc in encodings:
            for sep in separators:
                try:
                    if sep is None:
                        df = pd.read_csv(io.BytesIO(content), encoding=enc, sep=None, engine='python', on_bad_lines='skip')
                    else:
                        df = pd.read_csv(io.BytesIO(content), encoding=enc, sep=sep, on_bad_lines='skip')
                    
                    if df is not None and not df.empty and len(list(df.columns)) > 1:
                        return df
                except Exception:
                    continue
    except Exception:
        pass
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    filters_data = []
    selected_filters = {}
    error_msg = None
    data_html = None

    if request.method == 'POST':
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            df = load_dataframe_from_file(file)

            if df is not None and not df.empty:
                try:
                    # ดึงรายชื่อคอลัมน์
                    col_names = [str(c) for c in list(df.columns)]

                    def clean_str(val):
                        if pd.isna(val):
                            return ""
                        if isinstance(val, float) and val.is_integer():
                            return str(int(val))
                        return str(val).strip()

                    # สร้างตัวเลือก Filter
                    for col in col_names:
                        try:
                            raw_vals = df[col].dropna().unique().tolist()
                            sorted_vals = sorted(raw_vals, key=lambda x: (isinstance(x, str), str(x)))
                        except Exception:
                            sorted_vals = df[col].dropna().unique().tolist()
                        
                        filters_data.append({
                            'column': col,
                            'values': sorted_vals
                        })

                    # รับค่า Filter จากฟอร์ม
                    for key in request.form:
                        if key.startswith('filter_'):
                            c_name = key.replace('filter_', '')
                            val = request.form.get(key)
                            if val and val != 'ALL':
                                selected_filters[c_name] = val

                    # กรองข้อมูล
                    filtered_df = df.copy()
                    for col, selected_val in selected_filters.items():
                        if col in filtered_df.columns:
                            filtered_df = filtered_df[filtered_df[col].apply(clean_str) == str(selected_val).strip()]

                    data_html = filtered_df.to_html(classes='table table-striped table-hover', index=False)

                except Exception as e:
                    error_msg = f"เกิดข้อผิดพลาดในการประมวลผลข้อมูล: {str(e)}"
            else:
                error_msg = "ไม่สามารถอ่านโครงสร้างข้อมูลในไฟล์ได้ กรุณาตรวจสอบไฟล์อีกครั้ง"

    return render_template('index.html', 
                           data_html=data_html, 
                           filters_data=filters_data, 
                           selected_filters=selected_filters, 
                           error_msg=error_msg)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
import os
import io
from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__, template_folder='../templates')

# ใช้ Dictionary เก็บข้อมูลแบบปลอดภัย
store = {}

@app.route('/', methods=['GET', 'POST'])
def index():
    filters_data = []
    selected_filters = {}
    error_msg = None
    data_html = None

    if request.method == 'POST':
        action = request.form.get('action')
        
        # ถ้านดปุ่มล้างข้อมูล
        if action == 'clear' or action == 'reset':
            store.clear()
            return render_template('index.html', data_html=None, filters_data=[], selected_filters={})

        # 1. กรณีอัปโหลดไฟล์ใหม่
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            try:
                content = file.read()
                encodings = ['utf-8', 'tis-620', 'cp874', 'utf-8-sig', 'latin1']
                separators = [None, '\t', ',', ';']
                
                df_loaded = None
                
                for enc in encodings:
                    for sep in separators:
                        try:
                            if sep is None:
                                df_loaded = pd.read_csv(io.BytesIO(content), encoding=enc, sep=None, engine='python', on_bad_lines='skip')
                            else:
                                df_loaded = pd.read_csv(io.BytesIO(content), encoding=enc, sep=sep, on_bad_lines='skip')
                            
                            if df_loaded is not None and not df_loaded.empty and len(list(df_loaded.columns)) > 1:
                                break
                        except Exception:
                            continue
                    if df_loaded is not None and not df_loaded.empty and len(list(df_loaded.columns)) > 1:
                        break

                if df_loaded is not None and not df_loaded.empty:
                    store['df'] = df_loaded
                else:
                    store.clear()
                    error_msg = "ไม่สามารถอ่านโครงสร้างข้อมูลในไฟล์ได้ กรุณาตรวจสอบไฟล์อีกครั้ง"

            except Exception as e:
                store.clear()
                error_msg = f"ไม่สามารถอ่านไฟล์ได้: {str(e)}"

        # 2. กรณีเลือกตัวกรอง
        for key in request.form:
            if key.startswith('filter_'):
                col_name = key.replace('filter_', '')
                val = request.form.get(key)
                if val and val != 'ALL':
                    selected_filters[col_name] = val

    # ประมวลผลและสร้างตัวกรอง
    if 'df' in store and store['df'] is not None and not store['df'].empty:
        try:
            df = store['df']
            cols = [str(c) for c in list(df.columns)]
            filtered_df = df.copy()

            def clean_str(val):
                if pd.isna(val):
                    return ""
                if isinstance(val, float) and val.is_integer():
                    return str(int(val))
                return str(val).strip()

            # สร้างรายการตัวกรองสำหรับทุกคอลัมน์
            for col in cols:
                try:
                    raw_vals = df[col].dropna().unique().tolist()
                    sorted_vals = sorted(raw_vals, key=lambda x: (isinstance(x, str), str(x)))
                except Exception:
                    sorted_vals = df[col].dropna().unique().tolist()
                
                filters_data.append({
                    'column': col,
                    'values': sorted_vals
                })

            # กรองข้อมูลตามที่เลือก
            for col, selected_val in selected_filters.items():
                if col in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df[col].apply(clean_str) == str(selected_val).strip()]

            data_html = filtered_df.to_html(classes='table table-striped table-hover', index=False)
        except Exception as e:
            store.clear()
            error_msg = f"เกิดข้อผิดพลาดในการประมวลผลข้อมูล: {str(e)}"

    return render_template('index.html', 
                           data_html=data_html, 
                           filters_data=filters_data, 
                           selected_filters=selected_filters, 
                           error_msg=error_msg)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
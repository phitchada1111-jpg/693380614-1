import os
import io
from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__, template_folder='../templates')

global_df = None

@app.route('/', methods=['GET', 'POST'])
def index():
    global global_df
    col_list = []
    filters_data = []
    selected_filters = {}
    error_msg = None

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'clear':
            global_df = None
            return render_template('index.html', data_html=None, filters_data=[], selected_filters={})

        # 1. จัดการอัปโหลดไฟล์ (.csv / .txt)
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
                            
                            if df_loaded is not None and len(df_loaded.columns) > 1:
                                break
                        except Exception:
                            continue
                    if df_loaded is not None and len(df_loaded.columns) > 1:
                        break

                if df_loaded is not None and not df_loaded.empty:
                    global_df = df_loaded
                else:
                    error_msg = "ไม่สามารถอ่านโครงสร้างข้อมูลในไฟล์ได้ กรุณาตรวจสอบไฟล์อีกครั้ง"

            except Exception as e:
                error_msg = f"ไม่สามารถอ่านไฟล์ได้: {str(e)}"

        # 2. รับค่าจากตัวกรอง
        for key in request.form:
            if key.startswith('filter_'):
                col_name = key.replace('filter_', '')
                val = request.form.get(key)
                if val and val != 'ALL':
                    selected_filters[col_name] = val

    if global_df is not None and not global_df.empty:
        try:
            col_list = [str(c) for c in global_df.columns.tolist()]
            filtered_df = global_df.copy()

            def clean_str(val):
                if pd.isna(val):
                    return ""
                if isinstance(val, float) and val.is_integer():
                    return str(int(val))
                return str(val).strip()

            for c_name in col_list:
                try:
                    raw_values = global_df[c_name].dropna().unique().tolist()
                    sorted_vals = sorted(raw_values, key=lambda x: (isinstance(x, str), str(x)))
                except Exception:
                    sorted_vals = global_df[c_name].dropna().unique().tolist()
                
                filters_data.append({
                    'column': c_name,
                    'values': sorted_vals
                })

            for c_name, selected_val in selected_filters.items():
                if c_name in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df[c_name].apply(clean_str) == str(selected_val).strip()]

            data_html = filtered_df.to_html(classes='table table-striped table-hover', index=False)
            return render_template('index.html', 
                                   data_html=data_html, 
                                   filters_data=filters_data, 
                                   selected_filters=selected_filters,
                                   error_msg=error_msg)
        except Exception as e:
            error_msg = f"เกิดข้อผิดพลาดในการประมวลผลข้อมูล: {str(e)}"

    return render_template('index.html', data_html=None, filters_data=[], selected_filters={}, error_msg=error_msg)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
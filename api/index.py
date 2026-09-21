import os
from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__, template_folder='../templates')

global_df = None

@app.route('/', methods=['GET', 'POST'])
def index():
    global global_df
    columns = []
    filters_data = []
    selected_filters = {}

    if request.method == 'POST':
        # เช็คว่ากดปุ่ม Clear หรือไม่
        action = request.form.get('action')
        if action == 'clear':
            global_df = None
            return render_template('index.html', data_html=None, filters_data=[], selected_filters={})

        # 1. จัดการการอัปโหลดไฟล์ CSV
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            try:
                global_df = pd.read_csv(file, sep=None, engine='python', on_bad_lines='skip')
            except Exception as e:
                return f"เกิดข้อผิดพลาดในการอ่านไฟล์: {str(e)}"

        # 2. รับค่าตัวกรองทั้งหมดที่ส่งมาจากฟอร์ม (ส่งมาในรูปแบบ filter_<column_name>)
        for key in request.form:
            if key.startswith('filter_'):
                col_name = key.replace('filter_', '')
                val = request.form.get(key)
                if val and val != 'ALL':
                    selected_filters[col_name] = val

    if global_df is not None:
        columns = global_df.columns.tolist()
        filtered_df = global_df.copy()

        # ฟังก์ชันช่วยจัดการเปรียบเทียบ string และเลขทศนิยม (.0)
        def clean_str(val):
            if pd.isna(val):
                return ""
            if isinstance(val, float) and val.is_integer():
                return str(int(val))
            return str(val).strip()

        # สร้างรายการข้อมูลตัวเลือก (Unique Values) สำหรับแต่ละคอลัมน์เพื่อนำไปสร้าง Dropdown
        for col in columns:
            try:
                raw_values = global_df[col].dropna().unique().tolist()
                sorted_vals = sorted(raw_values, key=lambda x: (isinstance(x, str), x))
            except Exception:
                sorted_vals = global_df[col].dropna().unique().tolist()
            
            filters_data.append({
                'column': col,
                'values': sorted_vals
            })

        # กรองข้อมูลตามเงื่อนไขที่เลือกในทุกๆ คอลัมน์
        for col, selected_val in selected_filters.items():
            if col in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[col].apply(clean_str) == str(selected_val).strip()]

        data_html = filtered_df.to_html(classes='table table-striped table-hover', index=False)
        return render_template('index.html', 
                               data_html=data_html, 
                               filters_data=filters_data, 
                               selected_filters=selected_filters)

    return render_template('index.html', data_html=None, filters_data=[], selected_filters={})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
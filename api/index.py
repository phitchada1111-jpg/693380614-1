import os
from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__, template_folder='../templates')

global_df = None

@app.route('/', methods=['GET', 'POST'])
def index():
    global global_df
    selected_column = None
    selected_value = None
    columns = []
    unique_values = []

    if request.method == 'POST':
        # 1. จัดการการอัปโหลดไฟล์ CSV
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            try:
                global_df = pd.read_csv(file, sep=None, engine='python', on_bad_lines='skip')
            except Exception as e:
                return f"เกิดข้อผิดพลาดในการอ่านไฟล์: {str(e)}"

        # 2. รับค่าคอลัมน์และค่าที่ต้องการกรอง
        selected_column = request.form.get('selected_column')
        selected_value = request.form.get('selected_value')

    if global_df is not None:
        columns = global_df.columns.tolist()
        
        # ถ้ายังไม่ได้เลือกคอลัมน์ ให้ใช้คอลัมน์แรกเป็นค่าเริ่มต้น
        if not selected_column or selected_column not in columns:
            selected_column = columns[0]

        # ดึงค่า unique ของคอลัมน์ที่เลือก
        unique_values = global_df[selected_column].dropna().unique().tolist()

        filtered_df = global_df.copy()

        # กรองข้อมูลตามค่าที่เลือก
        if selected_value and selected_value != 'ALL':
            filtered_df = filtered_df[filtered_df[selected_column].astype(str) == str(selected_value)]

        data_html = filtered_df.to_html(classes='table table-striped table-hover', index=False)
        return render_template('index.html', 
                               data_html=data_html, 
                               columns=columns, 
                               selected_column=selected_column, 
                               unique_values=unique_values, 
                               selected_value=selected_value)

    return render_template('index.html', data_html=None, columns=[], unique_values=[])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
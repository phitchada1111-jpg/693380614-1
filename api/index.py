from flask import Flask, render_template, request
import pandas as pd
import json

app = Flask(__name__, template_folder='../templates')

# ตัวแปรเก็บข้อมูลชั่วคราวในหน่วยความจำ
global_df = None

@app.route('/', methods=['GET', 'POST'])
def index():
    global global_df
    data_html = None
    modules = []
    selected_module = None
    
    if request.method == 'POST':
        # 1. จัดการการอัปโหลดไฟล์ CSV
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            try:
                # อ่านไฟล์ CSV ผ่าน pandas
                global_df = pd.read_csv(file, sep=None, engine='python', on_bad_lines='skip')
            except Exception as e:
                return f"เกิดข้อผิดพลาดในการอ่านไฟล์: {str(e)}"
        
        # 2. จัดการการกรองข้อมูลตาม Module/Category
        selected_module = request.form.get('module_filter')

    if global_df is not None:
        # ดึงรายการ Module/กลุ่มข้อมูล เพื่อใช้สร้างตัวเลือก Filter
        # (สมมติว่าไฟล์ CSV มีคอลัมน์ชื่อ 'Module' หรือ 'Category')
        filter_column = 'Module' if 'Module' in global_df.columns else global_df.columns[0]
        modules = global_df[filter_column].unique().tolist()
        
        filtered_df = global_df.copy()
        
        # กรองข้อมูลตาม Module ที่เลือก
        if selected_module and selected_module != 'ALL':
            filtered_df = filtered_df[filtered_df[filter_column] == selected_module]
            
        # แปลงเป็น HTML Table สำหรับนำไปแสดงในหน้า Dashboard
        data_html = filtered_df.to_html(classes='table table-striped table-hover', index=False)

    return render_template('index.html', data_html=data_html, modules=modules, selected_module=selected_module)

# สำหรับรัน Local
if __name__ == '__main__':
    app.run(debug=True)
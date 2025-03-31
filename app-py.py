import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
import pandas as pd
import tempfile
from datetime import datetime

# Create Flask application
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random string in production

# Database configuration
DATABASE = 'bom_database.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper functions
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    with app.app_context():
        conn = get_db_connection()
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()

# Initialize the database if it doesn't exist
if not os.path.exists(DATABASE):
    init_db()

# Routes
@app.route('/')
def index():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM bom_items').fetchall()
    conn.close()
    return render_template('index.html', items=items)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            try:
                # Process the Excel file
                df = pd.read_excel(filepath, engine='openpyxl')
                required_columns = ['Design Title', 'Description', 'Type', 'Designator', 
                                   'Qty on BOM', 'Manufacturer', 'Part Number']
                
                # Check if all required columns exist
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    flash(f'Missing columns: {", ".join(missing_columns)}')
                    return redirect(request.url)
                
                # Insert data into the database
                conn = get_db_connection()
                for _, row in df.iterrows():
                    conn.execute(
                        'INSERT INTO bom_items (design_title, description, type, designator, qty, manufacturer, part_number) VALUES (?, ?, ?, ?, ?, ?, ?)',
                        (row['Design Title'], row['Description'], row['Type'], row['Designator'], 
                         row['Qty on BOM'], row['Manufacturer'], row['Part Number'])
                    )
                conn.commit()
                conn.close()
                
                flash(f'Successfully uploaded {len(df)} items')
                return redirect(url_for('index'))
            
            except Exception as e:
                flash(f'Error processing file: {str(e)}')
                return redirect(request.url)
            finally:
                # Clean up the uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
    
    return render_template('upload.html')

@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        design_title = request.form['design_title']
        description = request.form['description']
        item_type = request.form['type']
        designator = request.form['designator']
        qty = request.form['qty']
        manufacturer = request.form['manufacturer']
        part_number = request.form['part_number']
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO bom_items (design_title, description, type, designator, qty, manufacturer, part_number) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (design_title, description, item_type, designator, qty, manufacturer, part_number)
        )
        conn.commit()
        conn.close()
        
        flash('Item added successfully')
        return redirect(url_for('index'))
    
    return render_template('add_item.html')

@app.route('/filter')
def filter_items():
    filter_column = request.args.get('column', '')
    filter_value = request.args.get('value', '')
    
    if not filter_column or not filter_value:
        return redirect(url_for('index'))
    
    valid_columns = ['design_title', 'description', 'type', 'designator', 'qty', 'manufacturer', 'part_number']
    if filter_column not in valid_columns:
        flash('Invalid filter column')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    items = conn.execute(
        f'SELECT * FROM bom_items WHERE {filter_column} LIKE ?', 
        (f'%{filter_value}%',)
    ).fetchall()
    conn.close()
    
    return render_template('index.html', items=items, filter_applied=True, 
                          filter_column=filter_column, filter_value=filter_value)

@app.route('/export')
def export_data():
    filter_column = request.args.get('column', '')
    filter_value = request.args.get('value', '')
    
    conn = get_db_connection()
    
    if filter_column and filter_value:
        valid_columns = ['design_title', 'description', 'type', 'designator', 'qty', 'manufacturer', 'part_number']
        if filter_column in valid_columns:
            items = conn.execute(
                f'SELECT * FROM bom_items WHERE {filter_column} LIKE ?', 
                (f'%{filter_value}%',)
            ).fetchall()
        else:
            items = conn.execute('SELECT * FROM bom_items').fetchall()
    else:
        items = conn.execute('SELECT * FROM bom_items').fetchall()
    
    conn.close()
    
    # Convert to pandas DataFrame
    df = pd.DataFrame([dict(item) for item in items])
    
    # Rename columns to match expected format
    column_mapping = {
        'design_title': 'Design Title',
        'description': 'Description',
        'type': 'Type',
        'designator': 'Designator',
        'qty': 'Qty on BOM',
        'manufacturer': 'Manufacturer',
        'part_number': 'Part Number'
    }
    df = df.rename(columns=column_mapping)
    
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
    temp_file.close()
    
    # Write to Excel
    df.to_excel(temp_file.name, index=False, engine='openpyxl')
    
    # Generate a meaningful filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    download_name = f'bom_export_{timestamp}.xlsx'
    
    return send_file(temp_file.name, as_attachment=True, download_name=download_name)

if __name__ == '__main__':
    app.run(debug=True)

from back.database import create_connection
from tkinter import filedialog, messagebox
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate
from reportlab.lib.pagesizes import landscape, A4
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl import load_workbook
from textwrap import wrap
import pandas as pd
import tempfile
import sys
import os
import time

def generate_report(modulo, cliente, setor, mes, status):
    conn = create_connection()
    if not conn:
        return []

    query = "SELECT * FROM bo_records WHERE modulo LIKE ? AND D_E_L_E_T_ <> '*'"
    params = [modulo]

    if cliente != "Todos":
        query += " AND loja = ?"
        params.append(cliente)
    if setor != "Todos":
        query += " AND setor_responsavel = ?"
        params.append(setor)
    if mes != "Todos":
        query += " AND MONTH(emissao_totvs) = ?"
        params.append(int(mes))
    if status != "Todos":
        query += " AND [status] = ?"
        params.append(status)

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    finally:
        conn.close()

def get_all_clients(ultimo_modulo):
    conn = create_connection()
    if not conn:
        return ["Todos"]

    query = "SELECT COALESCE(loja, 'Não especificado') AS Setor FROM bo_records WHERE loja IS NOT NULL AND loja NOT LIKE '' AND modulo LIKE ? AND D_E_L_E_T_ <> '*' GROUP BY loja"
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, ultimo_modulo)
            return ["Todos"] + [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()

def get_all_setores(ultimo_modulo):
    conn = create_connection()
    if not conn:
        return ["Todos"]

    query = "SELECT COALESCE(setor_responsavel, 'Não especificado') AS Setor FROM bo_records WHERE setor_responsavel IS NOT NULL AND setor_responsavel NOT LIKE '' AND modulo LIKE ? AND D_E_L_E_T_ <> '*' GROUP BY setor_responsavel"
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, ultimo_modulo)
            return ["Todos"] + [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()

def get_all_status(ultimo_modulo):
    conn = create_connection()
    if not conn:
        return ["Todos"]

    query = "SELECT COALESCE([status], 'Não especificado') AS [Status] FROM bo_records WHERE [status] IS NOT NULL AND [status] NOT LIKE '' AND modulo LIKE ? AND D_E_L_E_T_ <> '*' GROUP BY [status]"
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, ultimo_modulo)
            return ["Todos"] + [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()

def get_all_months():
    return ["Todos"] + [str(i) for i in range(1, 13)]

def export_to_pdf(data, headers, file_path):
    doc = SimpleDocTemplate(file_path, pagesize=landscape(A4))
    elements = []

    # Adiciona cabeçalho como primeira linha
    table_data = [headers] + data

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#24577f'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#ffffff'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#ffffff'),
        ('TEXTCOLOR', (0, 1), (-1, -1), '#000000'),
        ('GRID', (0, 0), (-1, -1), 1, '#000000'),
    ]))
    elements.append(table)

    doc.build(elements)
    return True

def export_to_excel(data, headers, file_path):
    df = pd.DataFrame(data, columns=headers)
    df.to_excel(file_path, index=False)

    # Formatação avançada
    wb = load_workbook(file_path)
    if wb.sheetnames:
        ws = wb[wb.sheetnames[0]]
    else:
        raise ValueError("No worksheets found in the Excel file.")

    header_font = Font(bold=True)
    header_fill = PatternFill(start_color="C0C0C0", end_color="C0C0C0", fill_type="solid")
    row_fills = [PatternFill(start_color="FFFFFF", fill_type="solid"),
                 PatternFill(start_color="FFFFE0", fill_type="solid")]
    border = Border(left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin'))

    for row_idx, row in enumerate(ws.iter_rows(), start=1):
        for cell in row:
            cell.border = border
            cell.alignment = Alignment(wrap_text=True, vertical='center')
            if row_idx == 1:
                cell.font = header_font
                cell.fill = header_fill
            else:
                cell.fill = row_fills[(row_idx - 2) % 2]

    from openpyxl.utils import get_column_letter

    for idx, col in enumerate(ws.columns, 1):
        max_length = 0
        column = get_column_letter(idx)
        for cell in col:
            if cell.value:
                lines = str(cell.value).split('\n')
                current_length = max(len(line) for line in lines)
                if current_length > max_length:
                    max_length = current_length
        ws.column_dimensions[column].width = max_length + 2

    wb.save(file_path)
    return True

def print_report(data, headers, file_path=None):
    temp_dir = tempfile.gettempdir()
    temp_pdf_path = os.path.join(temp_dir, "temp_report.pdf")

    export_to_pdf(data, headers, temp_pdf_path)

    if sys.platform == "win32":
        os.startfile(temp_pdf_path, "print")
    else:
        subprocess.run(["lp", temp_pdf_path])

    time.sleep(5)

    if os.path.exists(temp_pdf_path):
        os.unlink(temp_pdf_path)
    return True
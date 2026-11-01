"""Export DEMO reports (not accredited laboratory certificates)."""
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from pathlib import Path
from html import escape
from docx import Document
from docx.shared import Pt, Cm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
import os

FONT_LOCATIONS=[
 '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
 '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
 'C:/Windows/Fonts/arial.ttf',
]

def lines_for_order(store,order):
    lines=[('Mã đơn',order['code']),('Tên công việc',order['name']),('Trạng thái',order['status'])]
    for key,label in [('scheduled','Ngày quan trắc'),('location','Địa điểm'),('owner','Người phụ trách')]:
        if order['data'].get(key):lines.append((label,str(order['data'][key])))
    if order['parent_id']:
        contract=store.get(order['parent_id'])
        if contract:lines.append(('Hợp đồng',f"{contract['code']} · {contract['name']}"))
    for sample in reversed(store.list('sample',parent_id=order['id'])):
        lines.append(('MẪU',f"{sample['code']} | {sample['name']} | {sample['status']}"))
        for ind in reversed(store.list('indicator',parent_id=sample['id'])):
            lines.append(('Chỉ tiêu',f"{ind['code']} · {ind['name']} · {ind['data'].get('method','')}"))
            for res in reversed(store.list('result',parent_id=ind['id'])):
                lines.append(('Kết quả',f"{res['data'].get('value','')} {res['data'].get('unit','')} / {res['status']}"))
    return lines


def docx_for_order(store,order):
    doc=Document()
    sec=doc.sections[0];sec.top_margin=Cm(1.7);sec.bottom_margin=Cm(1.7)
    doc.add_heading('LABMETRIX',0)
    doc.add_paragraph('BẢN MÔ PHỎNG · KHÔNG PHẢI PHIẾU KẾT QUẢ CHÍNH THỨC')
    doc.add_heading('TỔNG HỢP HỒ SƠ ĐƠN',level=1)
    table=doc.add_table(rows=0, cols=2);table.style='Table Grid'
    for k,v in lines_for_order(store,order):
        row=table.add_row();row.cells[0].text=k;row.cells[1].text=str(v)
    doc.add_paragraph('Dữ liệu giả phục vụ trình diễn. Không sử dụng cho hồ sơ khách hàng hoặc báo cáo VILAS.')
    bio=BytesIO();doc.save(bio);return bio.getvalue()


def pdf_for_order(store,order):
    font='Helvetica'
    for fn in FONT_LOCATIONS:
        if os.path.exists(fn):
            pdfmetrics.registerFont(TTFont('LMViet',fn));font='LMViet';break
    out=BytesIO(); c=canvas.Canvas(out,pagesize=(595,842))
    def header():
        c.setFillColor(HexColor('#0C807C'));c.rect(0,793,595,49,fill=1,stroke=0)
        c.setFillColor(HexColor('#FFFFFF'));c.setFont(font,19);c.drawString(35,811,'LABMETRIX - DEMO')
        c.setFillColor(HexColor('#263D50'));c.setFont(font,10)
    header(); y=765
    c.drawString(35,y,'BẢN TỔNG HỢP HỒ SƠ DEMO - KHÔNG PHÁT HÀNH THỰC');y-=26
    for label,value in lines_for_order(store,order):
        value=str(value)
        # Show long strings on multiple lines in a modest printable width.
        chunks=[];part=''
        for word in value.split():
            test=(part+' '+word).strip()
            if pdfmetrics.stringWidth(test,font,9)>390 and part:
                chunks.append(part);part=word
            else: part=test
        if part:chunks.append(part)
        if y-(max(1,len(chunks))*14)<55:
            c.showPage();header();y=765
        c.setFont(font,9);c.drawString(35,y,label[:29]);
        for j,line in enumerate(chunks or ['']):c.drawString(157,y-j*13,line)
        y-=max(1,len(chunks))*13+7
    c.save();return out.getvalue()


def archive_for_order(store,order):
    buf=BytesIO()
    with ZipFile(buf,'w',compression=ZIP_DEFLATED) as z:
        z.writestr('BAO_CAO_DEMO.docx',docx_for_order(store,order))
        z.writestr('BAO_CAO_DEMO.pdf',pdf_for_order(store,order))
        descendants=[order]
        for sample in store.list('sample',parent_id=order['id']):
            descendants.append(sample)
            for ind in store.list('indicator',parent_id=sample['id']):
                descendants.append(ind)
        for rec in descendants:
            for file in store.list_files(rec['id']):
                blob=store.file(file['id'])
                z.writestr(f"HO_SO/{rec['code']}/{file['id']}_{Path(file['filename']).name}",blob['content'])
    return buf.getvalue()

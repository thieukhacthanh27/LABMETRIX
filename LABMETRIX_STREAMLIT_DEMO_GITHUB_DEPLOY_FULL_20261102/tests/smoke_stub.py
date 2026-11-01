"""Smoke-executes all page render paths without Streamlit dependency installed.
Not a replacement for a real browser test; validates app logic and imports.
"""
from __future__ import annotations
import sys,runpy,types,os,datetime
from pathlib import Path
sys.path.insert(0,os.getcwd())
PAGES=['🏠 Tổng quan','📄 Hợp đồng','📋 Đơn quan trắc','🧪 Mẫu & tiếp nhận','🔬 Chỉ tiêu & kết quả',
       '✅ QA/QC & phê duyệt','📍 Theo dõi tiến độ','📎 Hồ sơ ảnh/PDF','📚 Phương pháp & kho',
       '📝 Công việc & bàn giao','📦 Báo cáo & xuất file','📜 Nhật ký']
class State(dict):
    def __getattr__(self,k):return self[k]
    def __setattr__(self,k,v):self[k]=v
class Stub(types.ModuleType):
    sidebar=None
    def __init__(self,page):
        super().__init__('streamlit');self.sidebar=self;self.secrets={};self.session_state=State();self.page=page
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def __getattr__(self,name):
        if name=='cache_resource':return lambda *args,**kw: (args[0] if args and callable(args[0]) else (lambda fn:fn))
        if name in ('form','expander'):return lambda *a,**kw:self
        if name=='tabs':return lambda labels:[self for l in labels]
        if name=='columns':return lambda count,**kw:[self for _ in range(count if isinstance(count,int) else len(count))]
        if name=='selectbox':
            def select(label,options,*a,**kw):
                opts=list(options)
                if label=='Đi tới phân hệ':return self.page
                if not opts:return None
                return opts[min(kw.get('index',0),len(opts)-1)]
            return select
        if name=='date_input':return lambda *a,**kw:kw.get('value',a[1] if len(a)>1 else datetime.date.today())
        if name=='number_input':return lambda *a,**kw:kw.get('value',1)
        if name=='text_input':return lambda *a,**kw:kw.get('value','')
        if name=='text_area':return lambda *a,**kw:kw.get('value','')
        if name in ('checkbox','button','download_button','form_submit_button'):return lambda *a,**kw:False
        if name in ('file_uploader','camera_input'):return lambda *a,**kw:None
        if name=='stop':raise RuntimeError('unexpected st.stop()')
        if name=='rerun':raise RuntimeError('unexpected st.rerun()')
        return lambda *a,**kw:None
if __name__=='__main__':
    for page in PAGES:
        s=Stub(page)
        sys.modules['streamlit']=s
        runpy.run_path('streamlit_app.py',run_name='__main__')
        print('OK',page)

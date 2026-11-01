"""LABMETRIX Community Cloud native Streamlit DEMO.

A distinct, public-safe demonstration of the core LABMETRIX work flows.
This does NOT run the original FastAPI /legacy code or represent a production LIMS.
"""
from __future__ import annotations
import os, re, csv
from datetime import datetime, date, timedelta, timezone
from io import BytesIO
from pathlib import Path
import pandas as pd
import streamlit as st
from db import Store, Conflict, Invalid
from exports import docx_for_order,pdf_for_order,archive_for_order

# Resolve bundled files relative to the application, not Streamlit's working directory.
BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / 'assets' / 'logo.png'
LOCAL_DB_PATH = BASE_DIR / 'runtime' / 'labmetrix_demo.sqlite3'

st.set_page_config(page_title='LABMETRIX | DEMO trực tuyến',page_icon='🧪',layout='wide',initial_sidebar_state='collapsed')

st.markdown('''<style>
.block-container {padding-top:1.25rem;padding-bottom:4rem;max-width:1450px}
[data-testid="stMetric"] {border:1px solid #d9e7e9;border-radius:13px;padding:12px;background:#fff}
h1,h2,h3 {color:#12334b}
[data-testid="stForm"] {background:#fff;border:1px solid #dce7e9;border-radius:12px;padding:1rem}
[data-testid="stSidebar"] {background:#eaf5f4}
.lm-alert {background:#eff8f7;border-left:4px solid #0b857d;padding:12px;border-radius:8px;margin-bottom:12px}
.lm-card {border:1px solid #dfe9ed;border-radius:14px;background:white;padding:1rem;margin:.4rem 0}
.lm-tag {font-size:.8rem;color:#46667a}
@media (max-width: 768px){
.block-container{padding:.8rem .65rem 4rem}
h1{font-size:1.55rem!important}
[data-testid="stMetric"]{padding:7px}
[data-testid="stMetricValue"]{font-size:1.45rem}
[data-testid="stHorizontalBlock"]{gap:.4rem}
}
</style>''', unsafe_allow_html=True)


def secret(key,default=''):
    v=os.getenv(key,'')
    if v:return v
    try:return st.secrets.get(key,default)
    except (FileNotFoundError,KeyError):return default

@st.cache_resource(show_spinner='Khởi tạo kho DEMO chung...')
def get_store(url):return Store(url)

url=secret('LABMETRIX_DATABASE_URL') or f'sqlite:///{LOCAL_DB_PATH.as_posix()}'
try:store=get_store(url)
except Exception as exc:
    st.error('Không thể mở cơ sở dữ liệu. Kiểm tra LABMETRIX_DATABASE_URL trong Streamlit Secrets.')
    st.code(str(exc)[:600]);st.stop()

roles=['Quản lý đơn','Quan trắc','Phòng phân tích','QA/QC','Trưởng phòng','Giám đốc','Super Admin (DEMO)']
if 'actor' not in st.session_state:st.session_state.actor='Nguyễn Văn A'
if 'page' not in st.session_state:st.session_state.page='🏠 Tổng quan'

code_required=secret('DEMO_ACCESS_CODE')
if code_required:
    if not st.session_state.get('access_ok'):
        st.title('🔐 LABMETRIX DEMO')
        st.info('Nhập mã truy cập thử nghiệm do người quản lý cung cấp. Chỉ sử dụng dữ liệu giả.')
        with st.form('gate'):
            pwd=st.text_input('Mã truy cập DEMO',type='password')
            sent=st.form_submit_button('Vào thử nghiệm',type='primary')
        if sent:
            from hmac import compare_digest
            if compare_digest(pwd,code_required):st.session_state.access_ok=True;st.rerun()
            else:st.error('Mã truy cập không đúng.')
        st.stop()

PAGES=['🏠 Tổng quan','📄 Hợp đồng','📋 Đơn quan trắc','🧪 Mẫu & tiếp nhận','🔬 Chỉ tiêu & kết quả',
       '✅ QA/QC & phê duyệt','📍 Theo dõi tiến độ','📎 Hồ sơ ảnh/PDF','📚 Phương pháp & kho',
       '📝 Công việc & bàn giao','📦 Báo cáo & xuất file','📜 Nhật ký']

with st.sidebar:
    if LOGO_PATH.is_file():
        st.image(str(LOGO_PATH),width=78)
    st.markdown('### LABMETRIX')
    st.caption('Bản trình diễn Streamlit · Dữ liệu giả')
    st.selectbox('Vai trò mô phỏng',roles,key='role')
    st.text_input('Tên người thao tác',key='actor')
    st.divider()
    st.caption('🟢 Kho dùng chung cho các phiên truy cập')
    if url.startswith('sqlite:'):
        st.warning('SQLite trên Streamlit Cloud: dữ liệu có thể bị mất khi app khởi động lại. Hãy cấu hình PostgreSQL cho bản dùng chung lâu dài.')
    else:st.success('Đã kết nối cơ sở dữ liệu dùng chung')
    if st.button('🔄 Tải dữ liệu mới từ máy chủ',use_container_width=True):st.rerun()
    st.caption('Vai trò chỉ để trình diễn; không phải phân quyền bảo mật thực.')

head1,head2=st.columns([1,5],vertical_alignment='center')
with head1:
    if LOGO_PATH.is_file():
        st.image(str(LOGO_PATH),width=64)
with head2:
    st.markdown('## LABMETRIX')
    st.caption('Quản lý phòng thí nghiệm & quan trắc | BẢN DEMO TRỰC TUYẾN')
st.markdown('<div class="lm-alert"><b>MÔI TRƯỜNG TRÌNH DIỄN.</b> Không sử dụng kết quả phân tích, tài khoản, chữ ký hoặc hồ sơ khách hàng thật. Mọi người được cấp quyền vào DEMO có thể xem nội dung dữ liệu giả được chia sẻ.</div>',unsafe_allow_html=True)
page=st.selectbox('Đi tới phân hệ',PAGES,key='page')
st.caption('📱 Điện thoại và PC dùng cùng đường dẫn ứng dụng; bố cục tự thích ứng. Bấm 🔄 để lấy thay đổi mới từ người dùng khác.')


def entity_label(x):return f"{x['code']} · {x['name']}"
def choices(kind,parent_id=None):return store.list(kind,parent_id=parent_id)
def pick(label,items,key,allow_empty=False):
    ids=[x['id'] for x in items]
    table={x['id']:x for x in items}
    if allow_empty:ids=[None]+ids
    if not ids:
        st.info('Chưa có hồ sơ phù hợp.');return None
    val=st.selectbox(label,ids,format_func=lambda i:entity_label(table[i]) if i is not None else 'Không liên kết',key=key)
    return table.get(val)

def fmt_day(d):
    try:return date.fromisoformat(str(d)).strftime('%d/%m/%Y')
    except Exception:return str(d or '—')

def submit_create(kind,name,**kw):
    try:
        rec=store.create(kind,name,actor=st.session_state.actor,**kw)
        st.success('Đã lưu vào kho chung: '+rec['code']);return rec
    except (Conflict,Invalid) as e:st.error(str(e))
    except Exception:st.error('Không thể lưu hồ sơ. Hãy kiểm tra kết nối cơ sở dữ liệu.')
    return None

def submit_change(row,**kw):
    try:
        rec=store.change(row['id'],row['revision'],actor=st.session_state.actor,**kw)
        st.success('Đã lưu lên máy chủ.');return rec
    except Conflict as e:st.warning(str(e)+' Dùng nút 🔄 để lấy bản mới nhất.')
    except Invalid as e:st.error(str(e))
    except Exception:st.error('Lỗi lưu dữ liệu.')
    return None

def show_table(items,columns=None):
    rows=[]
    for a in items:
        row={'Mã':a['code'],'Tên':a['name'],'Trạng thái':a['status'],'Cập nhật':a['updated_at'][:16].replace('T',' ')}
        if columns:
            for k,v in columns.items():row[v]=a['data'].get(k,'')
        rows.append(row)
    if rows:st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
    else:st.info('Chưa có dữ liệu')


def family(order):
    samples=store.list('sample',parent_id=order['id'])
    indicators=[i for s in samples for i in store.list('indicator',parent_id=s['id'])]
    results=[r for i in indicators for r in store.list('result',parent_id=i['id'])]
    return samples,indicators,results


def show_file_center(row):
    existing=store.list_files(row['id'])
    st.markdown(f"**Tệp đính kèm: {row['code']}**")
    for f in existing:
        blob=store.file(f['id'])
        st.download_button(f"⬇ {f['filename']} ({f['size']//1024} KB)",blob['content'],
          file_name=f['filename'],mime=f['mime'],key=f"dl-{row['id']}-{f['id']}")
    with st.form(f"upl-{row['id']}",clear_on_submit=True):
        incoming=st.file_uploader('Chọn ảnh, PDF hoặc DOCX giả (tối đa 2 MB/tệp)',
                            type=['jpg','jpeg','png','pdf','docx'],key=f'input-file-{row["id"]}')
        up=st.form_submit_button('Lưu tệp vào kho chung')
        if up and incoming:
            ext=Path(incoming.name).suffix.lower()
            mime={'.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.pdf':'application/pdf',
                  '.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}.get(ext,'')
            try:
                store.add_file(row['id'],incoming.name,mime,incoming.getvalue(),st.session_state.actor)
                st.success('Đã tải tệp lên kho chung.');st.rerun()
            except Invalid as e:st.error(str(e))
    if row['kind'] in ('order','sample'):
        with st.expander('📸 Chụp ảnh trực tiếp trên điện thoại'):
            shot=st.camera_input('Ảnh minh họa (DEMO)',key=f'cam-{row["id"]}')
            if shot and st.button('Lưu ảnh chụp',key=f'cam-save-{row["id"]}'):
                try:
                    store.add_file(row['id'],'anh_hien_truong_demo.jpg','image/jpeg',shot.getvalue(),st.session_state.actor)
                    st.success('Đã lưu ảnh DEMO');st.rerun()
                except Invalid as e:st.error(str(e))

if page=='🏠 Tổng quan':
    stat=store.stats()
    a,b,c,d=st.columns(4)
    a.metric('Hợp đồng',stat.get('contract',0))
    b.metric('Đơn quan trắc',stat.get('order',0))
    c.metric('Mẫu',stat.get('sample',0))
    d.metric('Chỉ tiêu / Kết quả',f"{stat.get('indicator',0)} / {stat.get('result',0)}")
    st.subheader('Công việc cần xử lý')
    pending=[x for x in store.list('result') if x['status'] in ['Chờ QA','Chờ Giám đốc','Chờ Trưởng phòng']]
    if pending:st.warning(f'{len(pending)} kết quả đang chờ duyệt DEMO')
    else:st.success('Chưa có kết quả chờ duyệt')
    contracts=store.list('contract')
    overdue=[x for x in contracts if x['data'].get('deadline') and x['data']['deadline']<date.today().isoformat() and x['status']!='Hoàn thành']
    st.write(f'**Hợp đồng quá hạn (theo ngày hạn trả):** {len(overdue)}')
    st.subheader('Tình trạng hồ sơ')
    if contracts:
        counts=pd.DataFrame({'Trạng thái':[x['status'] for x in contracts]}).value_counts('Trạng thái').reset_index(name='Số lượng')
        st.bar_chart(counts.set_index('Trạng thái'),y='Số lượng')
    st.subheader('Đơn gần đây')
    show_table(store.list('order')[:12],{'scheduled':'Ngày QT','owner':'Người phụ trách'})

elif page=='📄 Hợp đồng':
    st.header('Hợp đồng & yêu cầu thử nghiệm')
    with st.expander('➕ Lập hợp đồng DEMO',expanded=False):
        with st.form('new-contract',clear_on_submit=True):
            name=st.text_input('Khách hàng (dữ liệu giả)')
            descr=st.text_area('Nội dung công việc')
            col1,col2=st.columns(2)
            contact=col1.text_input('Người liên hệ')
            deadline=col2.date_input('Hạn trả',value=date.today()+timedelta(days=7))
            address=st.text_input('Địa điểm')
            if st.form_submit_button('Tạo hợp đồng',type='primary'):
                if name.strip():
                    if submit_create('contract',name,data={'description':descr,'contact':contact,
                         'deadline':deadline.isoformat(),'address':address}):st.rerun()
                else:st.error('Hãy nhập khách hàng')
    search=st.text_input('🔎 Tìm hợp đồng theo mã hoặc khách hàng',key='search-contract')
    allc=store.list('contract',search=search);show_table(allc,{'deadline':'Hạn trả'})
    st.subheader('Chi tiết / cập nhật')
    rec=pick('Chọn hợp đồng',allc,'contract-select')
    if rec:
        with st.form(f'edit-contract-{rec["id"]}'):
            name=st.text_input('Tên khách hàng',value=rec['name'])
            status=st.selectbox('Trạng thái', ['Mới','Đang thực hiện','Chờ duyệt','Hoàn thành','Đã hủy'],index=['Mới','Đang thực hiện','Chờ duyệt','Hoàn thành','Đã hủy'].index(rec['status']) if rec['status'] in ['Mới','Đang thực hiện','Chờ duyệt','Hoàn thành','Đã hủy'] else 0)
            description=st.text_area('Nội dung',value=rec['data'].get('description',''))
            deadline=st.date_input('Hạn trả',value=date.fromisoformat(rec['data'].get('deadline',date.today().isoformat())))
            contact=st.text_input('Người liên hệ',value=rec['data'].get('contact',''))
            if st.form_submit_button('Lưu thay đổi'):
                data={**rec['data'],'description':description,'deadline':deadline.isoformat(),'contact':contact}
                if submit_change(rec,name=name,status=status,data=data):st.rerun()
        linked=store.list('order',parent_id=rec['id'])
        st.caption(f'Đơn liên kết: {len(linked)}')
        show_table(linked)

elif page=='📋 Đơn quan trắc':
    st.header('Đơn quan trắc · Nhiều mẫu / một đơn')
    contracts=choices('contract')
    with st.expander('➕ Tạo đơn DEMO',expanded=False):
        with st.form('new-order',clear_on_submit=True):
            parent=pick('Hợp đồng liên kết (tùy chọn)',contracts,'parent-contract',True)
            title=st.text_input('Tên đợt/đơn quan trắc')
            col1,col2=st.columns(2)
            scheduled=col1.date_input('Ngày quan trắc',date.today())
            owner=col2.text_input('Nhân viên phụ trách',value=st.session_state.actor)
            location=st.text_input('Địa điểm')
            if st.form_submit_button('Tạo đơn',type='primary'):
                if title.strip():
                    if submit_create('order',title,parent_id=parent['id'] if parent else None,
                        data={'scheduled':scheduled.isoformat(),'owner':owner,'location':location}):st.rerun()
                else:st.error('Nhập tên đơn')
    orders=choices('order')
    show_table(orders,{'scheduled':'Ngày QT','location':'Địa điểm'})
    rec=pick('Xem đơn / cập nhật tiến độ',orders,'order-select')
    if rec:
        samples,inds,results=family(rec)
        a,b,c=st.columns(3);a.metric('Mẫu',len(samples));b.metric('Chỉ tiêu',len(inds));c.metric('Kết quả',len(results))
        with st.form(f'order-update-{rec["id"]}'):
            new_status=st.selectbox('Trạng thái đơn',['Mới','Đang thực hiện','Đang phân tích','Chờ duyệt','Hoàn thành','Đã hủy'],index=['Mới','Đang thực hiện','Đang phân tích','Chờ duyệt','Hoàn thành','Đã hủy'].index(rec['status']) if rec['status'] in ['Mới','Đang thực hiện','Đang phân tích','Chờ duyệt','Hoàn thành','Đã hủy'] else 0)
            if st.form_submit_button('Cập nhật trạng thái'):
                if submit_change(rec,status=new_status):st.rerun()
        st.subheader('Mẫu thuộc đơn');show_table(samples,{'type':'Nền mẫu'})

elif page=='🧪 Mẫu & tiếp nhận':
    st.header('Tiếp nhận và quản lý mẫu')
    orders=choices('order')
    if not orders:st.warning('Tạo đơn trước khi tạo mẫu.')
    else:
        with st.expander('➕ Thêm nhiều mẫu vào một đơn',expanded=False):
            with st.form('add-samples',clear_on_submit=True):
                order=pick('Đơn quan trắc',orders,'sample-parent')
                count=st.number_input('Số mẫu cần tạo (1–20)',min_value=1,max_value=20,value=1)
                typ=st.selectbox('Nền mẫu', ['NT','NM','NS','KT','KLV','KXQ'])
                point=st.text_input('Điểm lấy mẫu (mặc định 01)')
                taken=st.date_input('Ngày lấy mẫu',date.today())
                name=st.text_input('Tên mẫu / mô tả',value='Mẫu quan trắc DEMO')
                if st.form_submit_button('Tạo mẫu DEMO',type='primary') and order:
                    for i in range(int(count)):
                        store.create('sample',f'{name} {i+1}',parent_id=order['id'],
                            data={'type':typ,'location':point or f'Điểm {i+1:02d}','collected':taken.isoformat()},
                            status='Đã tiếp nhận',actor=st.session_state.actor)
                    st.success(f'Đã tạo {count} mẫu');st.rerun()
    samples=choices('sample')
    search=st.text_input('Tìm mẫu',key='search-sample')
    if search:samples=[x for x in samples if search.casefold() in (x['code']+' '+x['name']).casefold()]
    show_table(samples,{'type':'Nền mẫu','location':'Vị trí'})
    row=pick('Chi tiết mẫu',samples,'sample-detail')
    if row:
        st.info(f"Thuộc đơn: {store.get(row['parent_id'])['code'] if store.get(row['parent_id']) else '—'}")
        st.write('Chỉ tiêu:',', '.join(x['name'] for x in store.list('indicator',parent_id=row['id'])) or 'Chưa có')
        with st.form(f'sample-update-{row["id"]}'):
            stat=st.selectbox('Tình trạng mẫu',['Mới','Đã tiếp nhận','Đang phân tích','Chờ duyệt','Hoàn thành','Không đạt QC'],index=['Mới','Đã tiếp nhận','Đang phân tích','Chờ duyệt','Hoàn thành','Không đạt QC'].index(row['status']) if row['status'] in ['Mới','Đã tiếp nhận','Đang phân tích','Chờ duyệt','Hoàn thành','Không đạt QC'] else 0)
            if st.form_submit_button('Lưu trạng thái mẫu'):
                if submit_change(row,status=stat):st.rerun()

elif page=='🔬 Chỉ tiêu & kết quả':
    st.header('Chỉ tiêu, phương pháp và kết quả phân tích')
    samples=choices('sample');methods=choices('method')
    with st.expander('➕ Bóc tách / thêm chỉ tiêu',expanded=False):
        with st.form('new-indicator',clear_on_submit=True):
            parent=pick('Mẫu',samples,'ind-parent')
            name=st.text_input('Tên chỉ tiêu',value='pH')
            method=st.selectbox('Phương pháp', ['Chưa xác định']+[x['name'] for x in methods])
            unit=st.text_input('Đơn vị',value='mg/L')
            if st.form_submit_button('Thêm chỉ tiêu',type='primary') and parent:
                if submit_create('indicator',name,parent_id=parent['id'],data={'method':method,'unit':unit},status='Chờ kết quả'):st.rerun()
    inds=choices('indicator')
    show_table(inds,{'method':'Phương pháp','unit':'Đơn vị'})
    with st.expander('➕ Nhập kết quả DEMO',expanded=False):
        with st.form('new-result',clear_on_submit=True):
            ind=pick('Chỉ tiêu',inds,'result-parent')
            val=st.text_input('Giá trị đo',placeholder='Ví dụ: 7.2')
            unit=st.text_input('Đơn vị kết quả',value=ind['data'].get('unit','') if ind else '')
            qc=st.selectbox('Tự đánh giá QC (DEMO)',['Chưa đánh giá','Đạt','Không đạt'])
            analyst=st.text_input('Người phân tích',value=st.session_state.actor)
            if st.form_submit_button('Lưu kết quả và gửi QA',type='primary') and ind:
                if val.strip():
                    if submit_create('result',f"{ind['name']} · {val}",parent_id=ind['id'],
                        data={'value':val,'unit':unit,'qc':qc,'analyst':analyst},status='Chờ QA'):st.rerun()
                else:st.error('Chưa nhập giá trị')
    results=choices('result')
    show_table(results,{'value':'Giá trị','unit':'Đơn vị','qc':'QC'})
    st.caption('Giá trị kết quả đã nhập được giữ nguyên; nếu cần chỉnh, lập kết quả mới và để lại lịch sử thao tác.')

elif page=='✅ QA/QC & phê duyệt':
    st.header('Duyệt kết quả – quy trình mô phỏng')
    st.warning('Lựa chọn vai trò chỉ là DEMO; các nút dưới đây KHÔNG có giá trị phê duyệt hoặc chữ ký chính thức.')
    pending=[r for r in choices('result') if r['status'] in ['Chờ QA','Chờ Trưởng phòng','Chờ Giám đốc','Cần bổ sung']]
    show_table(pending,{'value':'Giá trị','qc':'QC'})
    rec=pick('Chọn kết quả chờ xử lý',pending,'pending-approval')
    if rec:
        st.write('**Kết quả gốc:**',rec['data'].get('value'),rec['data'].get('unit'),'— QC:',rec['data'].get('qc'))
        with st.form(f'approv-{rec["id"]}'):
            decision=st.selectbox('Quyết định DEMO',['Duyệt QA → Chờ Trưởng phòng','Duyệt Trưởng phòng → Chờ Giám đốc','Duyệt Giám đốc → Hoàn thành','Trả lại bổ sung'])
            reason=st.text_area('Ghi chú / lý do')
            if st.form_submit_button('Ghi nhận bước phê duyệt'):
                if rec['data'].get('qc')=='Không đạt' and 'Duyệt' in decision:
                    st.error('Kết quả QC không đạt: không duyệt được.')
                else:
                    next_status={'Duyệt QA → Chờ Trưởng phòng':'Chờ Trưởng phòng',
                                 'Duyệt Trưởng phòng → Chờ Giám đốc':'Chờ Giám đốc',
                                 'Duyệt Giám đốc → Hoàn thành':'Hoàn thành',
                                 'Trả lại bổ sung':'Cần bổ sung'}[decision]
                    valid={'Chờ QA':['Chờ Trưởng phòng','Cần bổ sung'],'Chờ Trưởng phòng':['Chờ Giám đốc','Cần bổ sung'],
                           'Chờ Giám đốc':['Hoàn thành','Cần bổ sung'],'Cần bổ sung':['Chờ Trưởng phòng','Cần bổ sung']}
                    if next_status not in valid.get(rec['status'],[]):st.error('Không thể bỏ qua bước phê duyệt.')
                    elif submit_change(rec,status=next_status,data={**rec['data'],'approval_note':reason,
                          'approved_by_demo':st.session_state.actor}):st.rerun()

elif page=='📍 Theo dõi tiến độ':
    st.header('Theo dõi truy vết đơn → mẫu → chỉ tiêu → kết quả')
    contracts=choices('contract')
    late=[x for x in contracts if x['data'].get('deadline','9999')<date.today().isoformat() and x['status']!='Hoàn thành']
    if late:st.error(f'Có {len(late)} hợp đồng DEMO quá hạn')
    else:st.success('Không có hợp đồng DEMO quá hạn')
    for order in choices('order'):
        samples,inds,results=family(order)
        finished=sum(x['status']=='Hoàn thành' for x in results)
        with st.expander(f"{order['code']} · {order['name']} — {len(samples)} mẫu · {len(results)}/{len(inds)} kết quả"):
            st.progress(min(1.0,len(results)/len(inds)) if inds else 0.0,
                        text=f'{len(results)}/{len(inds)} chỉ tiêu có kết quả')
            st.write('**Trạng thái đơn:**',order['status'])
            for sample in samples:
                st.markdown(f"- **{sample['code']}** {sample['name']} ({sample['status']})")
                for ind in store.list('indicator',parent_id=sample['id']):
                    rr=store.list('result',parent_id=ind['id'])
                    st.caption(f"   ↳ {ind['code']} {ind['name']} · {rr[0]['status'] if rr else 'Thiếu kết quả'}")

elif page=='📎 Hồ sơ ảnh/PDF':
    st.header('Kho hồ sơ DEMO chung')
    st.caption('Tệp được lưu trực tiếp trong cơ sở dữ liệu. Chỉ sử dụng ảnh và biểu mẫu giả.')
    items=choices('order')+choices('sample')
    rec=pick('Chọn đơn hoặc mẫu',items,'file-record')
    if rec:show_file_center(rec)

elif page=='📚 Phương pháp & kho':
    st.header('Thư viện phương pháp, thiết bị và hóa chất')
    tab1,tab2,tab3=st.tabs(['Phương pháp','Thiết bị','Hóa chất'])
    for tab,kind in [(tab1,'method'),(tab2,'equipment'),(tab3,'chemical')]:
        with tab:
            show_table(choices(kind))
            with st.form(f'new-{kind}',clear_on_submit=True):
                name=st.text_input('Tên danh mục',key=f'{kind}-name')
                group=st.selectbox('Nhóm', ['Hữu cơ','Hóa lý','Vi sinh','Kim loại','Quan trắc','Khác'],key=f'{kind}-group')
                amount=st.text_input('Đơn vị / số lượng / thông tin',key=f'{kind}-amount')
                expiry=st.date_input('Hạn dùng/hiệu chuẩn dự kiến',value=date.today()+timedelta(days=180),key=f'{kind}-exp')
                if st.form_submit_button('Thêm vào thư viện'):
                    if name.strip():
                        if submit_create(kind,name,data={'group':group,'quantity':amount,'expiry':expiry.isoformat()}):st.rerun()

elif page=='📝 Công việc & bàn giao':
    st.header('Công việc & bàn giao DEMO')
    tabs=st.tabs(['Việc cần làm','Bàn giao mẫu / kết quả'])
    with tabs[0]:
        with st.form('new-task',clear_on_submit=True):
            title=st.text_input('Tên công việc')
            owner=st.text_input('Người phụ trách',value=st.session_state.actor)
            deadline=st.date_input('Hạn hoàn thành',date.today()+timedelta(days=3))
            if st.form_submit_button('Giao việc') and title.strip():
                if submit_create('task',title,data={'owner':owner,'deadline':deadline.isoformat()}):st.rerun()
        tasks=choices('task');show_table(tasks,{'owner':'Người phụ trách','deadline':'Hạn'})
        row=pick('Cập nhật công việc',tasks,'task-detail')
        if row:
            if st.button('Đánh dấu hoàn thành'):
                if submit_change(row,status='Hoàn thành'):st.rerun()
    with tabs[1]:
        st.caption('Biên bản bàn giao điện tử mô phỏng. Không phải chữ ký số.')
        orders=choices('order')
        with st.form('handover',clear_on_submit=True):
            order=pick('Đơn liên quan',orders,'handover-order')
            kind=st.selectbox('Loại bàn giao',['Bàn giao mẫu','Bàn giao kết quả'])
            sender=st.text_input('Người giao',value=st.session_state.actor)
            receiver=st.text_input('Người nhận')
            reason=st.text_area('Ghi chú')
            accepted=st.checkbox('Xác nhận DEMO đã bàn giao')
            if st.form_submit_button('Ghi nhận bàn giao') and order:
                if accepted and receiver.strip():
                    if submit_create('handover',kind,parent_id=order['id'],status='Đã xác nhận DEMO',
                        data={'sender':sender,'receiver':receiver,'note':reason}):st.rerun()
                else:st.error('Nhập người nhận và đánh dấu xác nhận')
        show_table(choices('handover'))

elif page=='📦 Báo cáo & xuất file':
    st.header('Xuất báo cáo DEMO Word / PDF / ZIP')
    orders=choices('order');rec=pick('Chọn đơn',orders,'report-order')
    if rec:
        a,b,c=st.columns(3)
        a.download_button('📄 Tải Word',docx_for_order(store,rec),file_name=f'{rec["code"]}_DEMO.docx',
                          mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',use_container_width=True)
        b.download_button('📕 Tải PDF',pdf_for_order(store,rec),file_name=f'{rec["code"]}_DEMO.pdf',mime='application/pdf',use_container_width=True)
        c.download_button('📦 Tải ZIP hồ sơ',archive_for_order(store,rec),file_name=f'{rec["code"]}_DEMO.zip',mime='application/zip',use_container_width=True)
    st.divider()
    st.subheader('Xuất worklist & nhập mẫu từ Excel/CSV')
    samples=choices('sample')
    csv_data=pd.DataFrame([{'sample_code':s['code'],'sample_name':s['name'],
                   'sample_type':s['data'].get('type',''),'status':s['status']} for s in samples]).to_csv(index=False).encode('utf-8-sig')
    st.download_button('⬇ Xuất danh sách mẫu CSV',csv_data,file_name='LABMETRIX_DEMO_WORKLIST.csv',mime='text/csv')
    st.caption('Nhập Excel/CSV với các cột: order_code, sample_name, sample_type. Giới hạn 100 dòng/lần.')
    upload=st.file_uploader('Tệp worklist DEMO',type=['csv','xlsx'],key='worklist-upload')
    if upload:
        try:
            df=pd.read_excel(upload) if upload.name.endswith('xlsx') else pd.read_csv(upload)
            st.dataframe(df.head(15),hide_index=True,use_container_width=True)
            required={'order_code','sample_name','sample_type'}
            if not required.issubset(df.columns):st.error('Thiếu cột bắt buộc: '+', '.join(sorted(required-set(df.columns))))
            elif len(df)>100:st.error('Tối đa 100 dòng')
            elif st.button('Nhập các mẫu vào kho DEMO'):
                ordmap={x['code']:x for x in choices('order')};count=0;skipped=[]
                for _,r in df.fillna('').iterrows():
                    code=str(r['order_code']).strip(); name=str(r['sample_name']).strip();typ=str(r['sample_type']).strip().upper()
                    if code not in ordmap or not name or typ not in ['NT','NM','NS','KT','KLV','KXQ']:
                        skipped.append(code);continue
                    store.create('sample',name,parent_id=ordmap[code]['id'],data={'type':typ},actor=st.session_state.actor)
                    count+=1
                st.success(f'Đã nhập {count} mẫu; bỏ qua {len(skipped)} dòng không hợp lệ.');st.rerun()
        except Exception as e:st.error('Không đọc được tệp; kiểm tra định dạng và cột đầu vào.')

elif page=='📜 Nhật ký':
    st.header('Lịch sử thao tác DEMO')
    history=store.audit(limit=300)
    st.dataframe(pd.DataFrame([{'Thời gian':x['created_at'],'Người':x['actor'],
       'Thao tác':x['action'],'ID':x['entity_id'],'Chi tiết':x['detail']} for x in history]),
       hide_index=True,use_container_width=True)
    st.caption('Nhật ký thao tác ứng dụng DEMO, không phải hệ thống audit bảo mật hay chữ ký được chứng thực.')

st.divider()
st.caption('LABMETRIX · STREAMLIT DEMO · Không được dùng để phát hành kết quả chính thức / VILAS · Dữ liệu giả')

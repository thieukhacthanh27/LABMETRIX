"""A shared, transactional DEMO repository for Streamlit (SQLite local / PostgreSQL cloud).
All records are synthetic. This module is independent from Streamlit for testing.
"""
from __future__ import annotations
import json, os, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy import (create_engine, MetaData, Table, Column, Integer, String, Text,
                        LargeBinary, UniqueConstraint, select, insert, update, delete, func)
from sqlalchemy.exc import IntegrityError

TZ = timezone(timedelta(hours=7))
def now(): return datetime.now(TZ).isoformat(timespec='seconds')

class Conflict(Exception): pass
class Invalid(Exception): pass

meta = MetaData()
entities = Table('entities', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('kind', String(36), nullable=False),
    Column('code', String(80), nullable=False),
    Column('parent_id', Integer, nullable=True),
    Column('name', String(300), nullable=False),
    Column('status', String(60), nullable=False, default='Mới'),
    Column('data', Text, nullable=False, default='{}'),
    Column('revision', Integer, nullable=False, default=1),
    Column('created_at', String(40), nullable=False),
    Column('updated_at', String(40), nullable=False),
    UniqueConstraint('kind','code',name='uq_kind_code'))
files = Table('files', meta,
    Column('id', Integer, primary_key=True),
    Column('entity_id', Integer, nullable=False),
    Column('filename', String(255), nullable=False),
    Column('mime', String(120), nullable=False),
    Column('size', Integer, nullable=False),
    Column('content', LargeBinary, nullable=False),
    Column('created_at', String(40), nullable=False))
logs = Table('logs', meta,
    Column('id', Integer, primary_key=True),
    Column('entity_id', Integer, nullable=True),
    Column('action', String(80), nullable=False),
    Column('actor', String(100), nullable=False),
    Column('detail', Text, nullable=False),
    Column('created_at', String(40), nullable=False))

PREFIX={'contract':'HD','order':'D','sample':'M','indicator':'CT','result':'KQ',
        'method':'PP','equipment':'TB','chemical':'HC','task':'CV','handover':'BG'}

class Store:
    def __init__(self, url=None):
        url=url or os.getenv('LABMETRIX_DATABASE_URL') or 'sqlite:///runtime/labmetrix_demo.sqlite3'
        if url.startswith('postgres://'): url='postgresql+psycopg://' + url[len('postgres://'):]
        if url.startswith('postgresql://'):url='postgresql+psycopg://' + url[len('postgresql://'):]
        if url.startswith('sqlite:///'):
            dbpath=url[len('sqlite:///'):]
            if dbpath!=':memory:': Path(dbpath).parent.mkdir(parents=True,exist_ok=True)
        self.url=url
        kw={'pool_pre_ping':True}
        if url.startswith('sqlite:'):kw['connect_args']={'check_same_thread':False,'timeout':30}
        self.engine=create_engine(url,**kw)
        meta.create_all(self.engine)
        if url.startswith('sqlite:'):
            from sqlalchemy import text
            with self.engine.connect() as conn:
                conn.execute(text('PRAGMA journal_mode=WAL'))
        self.seed()

    @staticmethod
    def unpack(row):
        if row is None: return None
        r=dict(row._mapping)
        if 'data' in r:
            try:r['data']=json.loads(r['data'])
            except ValueError:r['data']={}
        return r

    @staticmethod
    def note(con, entity_id, action, actor, detail):
        con.execute(insert(logs).values(entity_id=entity_id, action=action,
                 actor=(actor or 'DEMO')[:100],detail=str(detail)[:2000],created_at=now()))

    def list(self,kind=None,parent_id=None,search='',status=None,limit=2000):
        q=select(entities).order_by(entities.c.id.desc()).limit(limit)
        if kind:q=q.where(entities.c.kind==kind)
        if parent_id is not None:q=q.where(entities.c.parent_id==int(parent_id))
        if status:q=q.where(entities.c.status==status)
        if search:
            from sqlalchemy import or_
            s=f'%{search.strip()}%'
            q=q.where(or_(entities.c.name.ilike(s),entities.c.code.ilike(s)))
        with self.engine.connect() as con:return [self.unpack(x) for x in con.execute(q).fetchall()]

    def get(self,entity_id):
        with self.engine.connect() as con:
            return self.unpack(con.execute(select(entities).where(entities.c.id==int(entity_id))).first())

    def create(self,kind,name,parent_id=None,data=None,status='Mới',code=None,actor='DEMO'):
        if kind not in PREFIX:raise Invalid('Loại hồ sơ không hợp lệ')
        if not name or not name.strip():raise Invalid('Cần nhập tên hồ sơ')
        if parent_id is not None:
            parent=self.get(parent_id)
            if not parent:raise Invalid('Hồ sơ cha không tồn tại')
            expected={'order':'contract','sample':'order','indicator':'sample','result':'indicator','handover':'order'}
            if kind in expected and parent['kind']!=expected[kind]:
                raise Invalid('Liên kết hồ sơ không đúng')
        code=code or f'TEMP-{uuid.uuid4().hex[:15]}'
        t=now()
        with self.engine.begin() as con:
            result=con.execute(insert(entities).values(kind=kind,name=name.strip()[:300],
                parent_id=parent_id, status=status,data=json.dumps(data or {},ensure_ascii=False),
                code=code,revision=1,created_at=t,updated_at=t))
            entity_id=result.inserted_primary_key[0]
            if code.startswith('TEMP-'):
                newcode=f'{PREFIX[kind]}-{datetime.now(TZ).strftime("%y")}.{entity_id:05d}'
                con.execute(update(entities).where(entities.c.id==entity_id).values(code=newcode))
            self.note(con,entity_id,'CREATE',actor,f'{kind}: {name}')
        return self.get(entity_id)

    def change(self,entity_id,revision,actor='DEMO',**fields):
        old=self.get(entity_id)
        if not old:raise Invalid('Không tìm thấy hồ sơ')
        allowed={'name','status','data','parent_id'}
        if not fields or any(k not in allowed for k in fields):raise Invalid('Trường cập nhật không hợp lệ')
        if 'data' in fields:fields['data']=json.dumps(fields['data'],ensure_ascii=False)
        if 'name' in fields:
            if not str(fields['name']).strip():raise Invalid('Tên không được để trống')
            fields['name']=str(fields['name']).strip()[:300]
        with self.engine.begin() as con:
            ans=con.execute(update(entities).where(entities.c.id==entity_id,
                entities.c.revision==revision).values(**fields,revision=revision+1,updated_at=now()))
            if ans.rowcount!=1:raise Conflict('Hồ sơ vừa được sửa từ thiết bị khác. Tải lại trước khi lưu.')
            self.note(con,entity_id,'UPDATE',actor,','.join(fields.keys()))
        return self.get(entity_id)

    def add_file(self,entity_id,filename,mime,content,actor='DEMO'):
        parent=self.get(entity_id)
        if not parent:raise Invalid('Hồ sơ không tồn tại')
        if len(content)>2*1024*1024:raise Invalid('Mỗi tệp DEMO tối đa 2 MB')
        if len(content)==0:raise Invalid('Tệp rỗng')
        mime_allow={'application/pdf','image/jpeg','image/png','application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
        if mime not in mime_allow:raise Invalid('Chỉ nhận PDF, JPG, PNG, DOCX')
        # Verify signatures; do not trust browser supplied MIME alone.
        valid=content.startswith(b'%PDF-') if mime=='application/pdf' else (
            content.startswith(b'\xff\xd8\xff') if mime=='image/jpeg' else (
            content.startswith(b'\x89PNG\r\n\x1a\n') if mime=='image/png' else content.startswith(b'PK\x03\x04')))
        if not valid:raise Invalid('Nội dung tệp không khớp định dạng')
        clean=Path(str(filename).replace('\\','/')).name[:150]
        with self.engine.begin() as con:
            res=con.execute(insert(files).values(entity_id=entity_id,filename=clean,mime=mime,
                    size=len(content),content=content,created_at=now()))
            file_id=res.inserted_primary_key[0]
            self.note(con,entity_id,'UPLOAD',actor,f'{clean}, {len(content)} bytes')
        return file_id

    def list_files(self,entity_id):
        q=select(files.c.id,files.c.entity_id,files.c.filename,files.c.mime,files.c.size,files.c.created_at).where(files.c.entity_id==entity_id).order_by(files.c.id.desc())
        with self.engine.connect() as con:return [dict(r._mapping) for r in con.execute(q)]

    def file(self,file_id):
        with self.engine.connect() as con:
            row=con.execute(select(files).where(files.c.id==file_id)).first()
            return dict(row._mapping) if row else None

    def audit(self,entity_id=None,limit=150):
        q=select(logs).order_by(logs.c.id.desc()).limit(limit)
        if entity_id:q=q.where(logs.c.entity_id==entity_id)
        with self.engine.connect() as con:return [dict(x._mapping) for x in con.execute(q)]

    def stats(self):
        with self.engine.connect() as con:
            a=con.execute(select(entities.c.kind,func.count()).group_by(entities.c.kind)).all()
        return dict(a)

    def seed(self):
        if self.list(kind='contract',limit=1):return
        # Entirely fictional examples; nothing copied from the real LABMETRIX project.
        c1=self.create('contract','Công ty Môi Trường Minh Họa',data={'deadline':(datetime.now(TZ)+timedelta(days=7)).date().isoformat(),'address':'Khu công nghiệp giả định','contact':'Nguyễn Văn A','description':'Quan trắc nước thải - DEMO'},status='Đang thực hiện',actor='SYSTEM')
        c2=self.create('contract','Nhà máy ABC (dữ liệu giả)',data={'deadline':(datetime.now(TZ)+timedelta(days=2)).date().isoformat(),'address':'Địa điểm mẫu','contact':'Nguyễn Văn B','description':'Quan trắc không khí - DEMO'},status='Đang thực hiện',actor='SYSTEM')
        o1=self.create('order','Đợt quan trắc quý IV',parent_id=c1['id'],data={'location':'Điểm giả lập','scheduled':datetime.now(TZ).date().isoformat(),'owner':'Nguyễn Văn A'},status='Đang thực hiện',actor='SYSTEM')
        o2=self.create('order','Quan trắc khí thải định kỳ',parent_id=c2['id'],data={'location':'Xưởng giả lập','scheduled':datetime.now(TZ).date().isoformat(),'owner':'Nguyễn Văn B'},status='Mới',actor='SYSTEM')
        samples=[]
        for order,t in [(o1,'NT'),(o1,'NM'),(o2,'KT')]:
            samples.append(self.create('sample',f'Mẫu {t} mô phỏng',parent_id=order['id'],data={'type':t,'location':'Điểm 01','collected':datetime.now(TZ).date().isoformat()},status='Đã tiếp nhận',actor='SYSTEM'))
        for s in samples:
            method='GC-MS' if s['data']['type']=='KT' else 'Phân tích minh họa'
            ind=self.create('indicator','pH' if s['data']['type']!='KT' else 'VOCs mô phỏng',parent_id=s['id'],data={'unit':'-' if s['data']['type']!='KT' else 'mg/Nm³','method':method},status='Chờ kết quả',actor='SYSTEM')
            if s==samples[0]:
                self.create('result','Kết quả pH',parent_id=ind['id'],data={'value':'7.1','unit':'-','qc':'Đạt','analyst':'Nguyễn Văn C'},status='Chờ QA',actor='SYSTEM')
        for name,group,unit in [('pH - nước','Hóa lý','-'),('VOCs - khí thải','Hữu cơ','mg/Nm³'),('Kim loại - ICP','Kim loại','mg/L')]:
            self.create('method',name,data={'group':group,'unit':unit,'sop':'SOP minh họa'},actor='SYSTEM')
        self.create('equipment','GC-MS Demo-01',data={'department':'Phòng phân tích','calibration':'2027-06-30'},actor='SYSTEM')
        self.create('equipment','Máy đo pH Demo-02',data={'department':'Phòng quan trắc','calibration':'2027-05-01'},actor='SYSTEM')
        self.create('chemical','Dung dịch chuẩn pH 7 (giả)',data={'group':'Hóa lý','quantity':'2 chai','expiry':'2027-02-01'},actor='SYSTEM')
        self.create('chemical','Chuẩn VOCs (giả)',data={'group':'Hữu cơ','quantity':'1 lọ','expiry':'2027-03-15'},actor='SYSTEM')

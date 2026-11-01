import tempfile, os, pytest
from datetime import datetime
from db import Store,Conflict,Invalid
from exports import docx_for_order,pdf_for_order,archive_for_order

@pytest.fixture
def store(tmp_path): return Store('sqlite:///'+str(tmp_path/'demo.sqlite'))

def test_seed(store):
    assert store.stats()['contract']==2
    assert len(store.list('sample'))>=3

def test_2_devices_share(store,tmp_path):
    phone=Store(store.url)
    pc=Store(store.url)
    con=phone.create('contract','KH TEST PHONE',data={'deadline':'2026-11-10'},actor='PHONE')
    order=phone.create('order','Đơn từ điện thoại',con['id'],actor='PHONE')
    assert pc.get(order['id'])['name']=='Đơn từ điện thoại'
    samp=pc.create('sample','NT-01',order['id'],data={'type':'NT'},actor='PC')
    assert phone.list('sample',parent_id=order['id'])[0]['id']==samp['id']
    ind=phone.create('indicator','pH',samp['id'],data={'unit':'-'},actor='PHONE')
    res=pc.create('result','pH đo được',ind['id'],data={'value':'7.2','unit':'-'},actor='PC')
    assert phone.list('result',parent_id=ind['id'])[0]['id']==res['id']
    assert 'KH TEST PHONE' in pc.get(con['id'])['name']

def test_optimistic_lock(store):
    row=store.list('order')[0]
    store.change(row['id'],row['revision'],actor='A',status='Đang thực hiện')
    with pytest.raises(Conflict):store.change(row['id'],row['revision'],actor='B',status='Đã duyệt')

def test_wrong_parent(store):
    with pytest.raises(Invalid):store.create('result','Bị sai',parent_id=store.list('contract')[0]['id'])

def test_upload_and_exports(store):
    order=store.list('order')[0]
    pdf=pdf_for_order(store,order)
    assert pdf.startswith(b'%PDF')
    assert docx_for_order(store,order).startswith(b'PK')
    store.add_file(order['id'],'test.pdf','application/pdf',b'%PDF-1.4 dummy DEMO only',actor='TEST')
    assert store.list_files(order['id'])[0]['filename']=='test.pdf'
    assert archive_for_order(store,order).startswith(b'PK')
    with pytest.raises(Invalid):store.add_file(order['id'],'bad.pdf','application/pdf',b'hello')

def test_audit(store):
    row=store.create('task','Tạo thử',actor='PC')
    store.change(row['id'],row['revision'],status='Đang xử lý',actor='PHONE')
    log=store.audit(row['id'])
    assert len(log)==2 and log[0]['actor']=='PHONE'

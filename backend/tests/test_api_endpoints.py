"""Session and RBAC integration tests, isolated from production data and services."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core import auth
from app.api.routes import leads
from app.services.lead_repository import LeadRepository


def data(response):
    return response.json()["data"]


@pytest.fixture
def clients(tmp_path, monkeypatch):
    repository = LeadRepository(tmp_path / 'leads.db')
    monkeypatch.setattr(leads, 'lead_repository', repository)
    monkeypatch.setattr(auth.settings, 'app_env', 'development')
    monkeypatch.setattr(auth.settings, 'auth_database_url', f'sqlite:///{tmp_path / "sessions.db"}')
    monkeypatch.setattr(auth.settings, 'database_url', '')
    from app.services.auth_service import get_auth_store
    get_auth_store.cache_clear()
    store = get_auth_store()
    store.create_user('marketing', 'marketing-test-passphrase', 'marketing')
    store.create_user('sales', 'sales-test-passphrase', 'sales')
    async def no_sheet(*args, **kwargs):
        return True
    monkeypatch.setattr(leads.sheets_service, 'append_lead', no_sheet)
    marketing, sales, anonymous = [TestClient(app) for _ in range(3)]
    assert marketing.post('/api/v1/auth/login', json={'username':'marketing', 'password':'marketing-test-passphrase'}).status_code == 200
    assert sales.post('/api/v1/auth/login', json={'username':'sales', 'password':'sales-test-passphrase'}).status_code == 200
    return marketing, sales, anonymous


def test_dashboard(clients):
    assert 'login-screen' in clients[2].get('/').text


def test_session_locked_and_logout(clients):
    marketing, sales, anon = clients
    assert anon.get('/api/v1/leads').status_code == 401
    assert sales.post('/api/v1/auth/login', json={'username':'marketing', 'password':'marketing-test-passphrase'}).status_code == 409
    assert data(sales.get('/api/v1/auth/me'))['role'] == 'sales'
    sales.cookies.set('salep_current_role', 'marketing')
    assert data(sales.get('/api/v1/auth/me'))['role'] == 'sales'
    token = sales.cookies.get(auth.COOKIE)
    sales.post('/api/v1/auth/logout')
    assert sales.get('/api/v1/leads').status_code == 401
    anon.cookies.set(auth.COOKIE, token)
    assert anon.get('/api/v1/leads').status_code == 401
    assert sales.post('/api/v1/auth/login', json={'username':'marketing', 'password':'marketing-test-passphrase'}).status_code == 200


def test_role_spoof_and_detail(clients):
    marketing, sales, _ = clients
    assert len(data(marketing.get('/api/v1/leads'))['items']) == 7
    result = data(sales.get('/api/v1/leads?role=marketing&status=invalid'))['items']
    assert len(result) == 4
    assert all(l['marketing_status']=='valid' for l in result)
    assert sales.get('/api/v1/leads/lead_demo_003').status_code == 404
    assert sales.get('/api/v1/leads/recent').status_code == 403
    assert 'pending' not in data(sales.get('/api/v1/leads/stats'))


def test_write_permissions(clients):
    marketing, sales, _ = clients
    assert sales.patch('/api/v1/leads/lead_demo_003/status', json={'marketing_status':'valid'}).status_code == 403


def test_write_origin_allows_configured_public_origin_behind_proxy(clients, monkeypatch):
    marketing, sales, _ = clients
    # Keep the local SQLite auth store for this contract test while exercising
    # the configured public origin used by production deployments.
    monkeypatch.setattr(auth.settings, 'app_env', 'development')
    monkeypatch.setattr(auth.settings, 'app_domain', 'salep-staging.icdigital.io')
    async def discover(*args, **kwargs):
        return {'matched': 0, 'saved': 0}
    monkeypatch.setattr('app.api.routes.spse.discover_spse_tenders', discover)

    allowed = marketing.post(
        '/api/v1/spse/search',
        json={'keywords': ['software'], 'limit': 1},
        headers={'Origin': 'https://salep-staging.icdigital.io'},
    )
    # The route may fail to fetch live SPSE in a test environment, but must pass
    # the origin check (502 is an upstream fetch failure; 403 is a bad origin).
    assert allowed.status_code == 200

    denied = marketing.post(
        '/api/v1/spse/search',
        json={'keywords': ['software'], 'limit': 1},
        headers={'Origin': 'https://attacker.example'},
    )
    assert denied.status_code == 403
    for path in ['/search','/leads/analyze','/leads/analyze-url','/scheduler/start','/scheduler/trigger']:
        assert sales.post('/api/v1'+path,json={}).status_code == 403
    assert sales.put('/api/v1/scheduler/config',json={}).status_code == 403
    assert sales.get('/api/v1/scheduler/status').status_code == 403
    assert marketing.patch('/api/v1/leads/lead_demo_001/sales-status',json={'sales_status':'Closing', 'note': 'Test catatan'}).status_code == 403
    assert sales.patch('/api/v1/leads/lead_demo_003/sales-status',json={'sales_status':'Closing', 'note': 'Test catatan'}).status_code == 404
    assert sales.patch('/api/v1/leads/lead_demo_001/sales-status',json={'sales_status':'garbage', 'note': 'Test catatan'}).status_code == 422
    assert sales.patch('/api/v1/leads/lead_demo_001/sales-status',json={'sales_status':'Closing', 'note': '  '}).status_code == 422
    assert sales.patch('/api/v1/leads/lead_demo_001/sales-status',json={'sales_status':'Closing', 'note': 'Sudah closing deal'}).status_code == 200


def test_qualification_and_pagination(clients):
    marketing, sales, _ = clients
    approved = marketing.patch(
        '/api/v1/leads/lead_demo_003/status',
        json={'marketing_status':'valid', 'review_note': 'Relevan dengan kebutuhan aplikasi.'},
    )
    assert approved.status_code == 200
    approved_data = data(approved)
    assert approved_data['marketing_reviewed_by_username'] == 'marketing'
    assert approved_data['marketing_reviewed_by_user_id']
    assert approved_data['marketing_review_note'] == 'Relevan dengan kebutuhan aplikasi.'
    assert approved_data['marketing_reviewed_at']
    assert sales.get('/api/v1/leads/lead_demo_003').status_code == 200
    marketing.patch('/api/v1/leads/lead_demo_003/status',json={'marketing_status':'invalid'})
    assert sales.get('/api/v1/leads/lead_demo_003').status_code == 404
    first_page = data(marketing.get('/api/v1/leads?limit=2&page=1'))
    second_page = data(marketing.get('/api/v1/leads?limit=2&page=2'))
    assert first_page['pagination'] == {'page': 1, 'limit': 2, 'total': 7}
    assert second_page['pagination'] == {'page': 2, 'limit': 2, 'total': 7}
    first = first_page['items']
    second = second_page['items']
    assert len(first)==len(second)==2
    assert not {l['lead_id'] for l in first}&{l['lead_id'] for l in second}
    assert len(data(marketing.get('/api/v1/leads?status=pending'))['items'])==1
    assert len(data(sales.get('/api/v1/leads?sales_status=Sedang%20Dihubungi'))['items'])==2
    assert len(data(marketing.get('/api/v1/leads?search=Brian'))['items'])==1


def test_search_validation(clients):
    m=clients[0]
    for payload in [dict(keywords=[' '],start_date='2026-10-01',end_date='2026-10-02'),dict(keywords=['hosting'],start_date='2026-10-04',end_date='2026-10-02')]:
        assert m.post('/api/v1/search',json=payload).status_code==422


def test_scheduler_config_saved(clients, tmp_path, monkeypatch):
    from app.api.routes import scheduler
    monkeypatch.setattr(scheduler,'CONFIG_PATH',tmp_path/'discovery.json')
    for attr in ['auto_search_keywords','auto_search_sources','auto_search_limit_per_run','auto_search_interval_minutes']:
        monkeypatch.setattr(scheduler.settings,attr,getattr(scheduler.settings,attr))
    response=clients[0].put('/api/v1/scheduler/config',json={'keywords':[' hosting ','managed service','hosting'],'sources':['threads'],'limit_per_run':5})
    assert response.status_code==200
    assert data(response)['keywords']==['hosting','managed service']
    assert data(response)['interval_minutes']==30
    assert (tmp_path/'discovery.json').exists()
    assert clients[0].put('/api/v1/scheduler/config',json={'keywords':[' '],'sources':['threads'],'limit_per_run':5}).status_code==422

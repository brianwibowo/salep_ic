from unittest.mock import AsyncMock
import asyncio
import pytest
from app.sources.threads_source import ThreadsSourceAdapter
from app.services.scheduler import LeadScheduler
from app.services import scheduler as scheduler_module
from app.services.lead_service import build_lead_record
from app.services.lead_repository import LeadRepository
from app.agent.schemas import RawLead, LeadAnalysis, IntentType, SearchResponse


@pytest.mark.parametrize('content',['Butuh hosting VPS untuk bisnis','Cari managed service server 24 jam','Rekomendasi vendor jaringan kantor','Butuh backup data dan pentest'])
def test_threads_accept_it_domains(content):
    lead = ThreadsSourceAdapter()._parse_item({'captionText':content,'postUrl':'https://www.threads.net/t/test'},'IT')
    assert lead and lead.content == content


def test_review_required_and_no_duplicates(tmp_path):
    raw = RawLead(source='threads',source_url='https://example.com/lead',content='Butuh managed service',matched_keyword='managed service')
    analysis = LeadAnalysis(is_potential_lead=True,intent=IntentType.LOOKING_FOR_VENDOR,needs=['managed service'],lead_score=95,confidence=.99)
    record=build_lead_record(raw,analysis)
    assert record.marketing_status=='pending'
    repo=LeadRepository(tmp_path/'test.db')
    repo.save_lead(record)
    assert repo.get_lead(record.lead_id)['marketing_status']=='pending'
    repo.update_marketing_status(record.lead_id,'valid')
    second=build_lead_record(raw,analysis)
    repo.save_lead(second)
    assert second.lead_id==record.lead_id
    assert repo.get_lead(record.lead_id)['marketing_status']=='valid'


@pytest.mark.asyncio
async def test_rotation_and_overlap(monkeypatch):
    monkeypatch.setattr(scheduler_module.settings,'auto_search_keywords','hosting,managed service,pentest')
    mock=AsyncMock(return_value=SearchResponse(query_id='test',total_found=0,total_analyzed=0,qualified=0,leads=[]))
    monkeypatch.setattr(scheduler_module,'run_search',mock)
    scheduler=LeadScheduler()
    await scheduler.run_cycle()
    await scheduler.run_cycle()
    assert mock.call_args_list[0].args[0].keywords==['hosting','managed service']
    assert mock.call_args_list[1].args[0].keywords==['pentest','hosting']
    async with scheduler._cycle_lock:
        assert (await scheduler.run_cycle())['status']=='busy'
    assert mock.await_count==2


@pytest.mark.asyncio
async def test_threads_queries_dates_and_errors(monkeypatch):
    import httpx
    from app.sources import threads_source
    calls=[]
    def handler(request):
        import json
        calls.append(json.loads(request.content)['searchQuery'])
        return httpx.Response(200,json=[
            {'captionText':'butuh hosting','postUrl':'https://example.com/old','takenAtISO':'2020-01-01T00:00:00Z'},
            {'captionText':'butuh server','postUrl':'https://example.com/new','takenAtISO':'2026-10-08T00:00:00Z'}])
    original=httpx.AsyncClient
    monkeypatch.setattr(threads_source.settings,'apify_api_token','test-token')
    monkeypatch.setattr(threads_source.httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(handler)))
    result=await ThreadsSourceAdapter().search(['hosting','managed service','pentest'],'2026-10-01','2026-10-08',10)
    assert calls==['hosting','managed service','pentest']
    assert len(result)==3 and all(l.source_url.endswith('/new') for l in result)
    monkeypatch.setattr(threads_source.httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(lambda request:httpx.Response(403))))
    with pytest.raises(RuntimeError,match='Apify'):
        await ThreadsSourceAdapter().search(['hosting'],'2026-10-01','2026-10-08',5)

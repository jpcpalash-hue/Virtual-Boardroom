import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
d = tempfile.mkdtemp(prefix='boardroom_test_')
os.environ['BOARDROOM_DB_PATH'] = str(Path(d) / 'test.db')
from fastapi.testclient import TestClient
from app import app

def test_chair_controls_and_history():
        client=TestClient(app)
        health=client.get('/api/health'); assert health.status_code==200
        res=client.post('/api/meetings',json={'title':'Choose vendor','agenda':'Should we invest in a new AI technology vendor?','context':'Budget constrained'})
        assert res.status_code==201, res.text
        mt=res.json(); assert 'technology' in mt['participants'] and 'devil' in mt['participants']
        assert client.get('/api/meetings/'+mt['id']).json()['title']=='Choose vendor'
        # OpenAI key missing -> no fabricated agent turns.
        old_key=os.environ.pop('OPENAI_API_KEY',None)
        try: assert client.post('/api/meetings/'+mt['id']+'/opening').status_code==503
        finally:
            if old_key: os.environ['OPENAI_API_KEY']=old_key
        approved=client.post('/api/meetings/'+mt['id']+'/decision',json={'decision':'Defer','rationale':'Need due diligence'})
        assert approved.status_code==200 and approved.json()['status']=='closed'
        assert client.post('/api/meetings/'+mt['id']+'/decision',json={'decision':'Approve'}).status_code==409
        exported=client.get('/api/meetings/'+mt['id']+'/export')
        assert exported.status_code==200 and 'Need due diligence' in exported.text
        assert client.get('/api/meetings').json()[0]['title']=='Choose vendor'

def test_selection_and_validation():
        from agents import select_participants
        assert 'devil' in select_participants('career offer salary')
        assert 'finance' in select_participants('career offer salary')
        assert TestClient(app).post('/api/meetings',json={'title':'X','agenda':'a'}).status_code==422


def test_roundtrip_with_mock_experts(monkeypatch):
    import app as server
    from engine import opening_round as actual_opening, debate_round as actual_debate
    import engine
    calls=[]
    async def fake_ask(agent_id, agenda, context, history, question, mode='opening'):
        calls.append((agent_id,mode,len(history)))
        return f'Opinion from {agent_id} during {mode}: check assumptions and assess alternatives.'
    monkeypatch.setattr(engine,'ask_agent',fake_ask)
    monkeypatch.setattr(server,'ask_agent',fake_ask)
    monkeypatch.setattr(server,'opening_round',actual_opening)
    monkeypatch.setattr(server,'debate_round',actual_debate)
    monkeypatch.setattr(server,'configured',lambda:True)
    client=TestClient(server.app)
    meeting=client.post('/api/meetings',json={'title':'Investment choice','agenda':'Should we launch a new business application?','context':'We have limited funding'}).json()
    mid=meeting['id']
    opened=client.post(f'/api/meetings/{mid}/opening'); assert opened.status_code==200
    assert len(opened.json()['messages'])==4
    assert len(calls)==4 and all(mode=='opening' for _,mode,_ in calls)
    assert client.post(f'/api/meetings/{mid}/opening').status_code==409
    debated=client.post(f'/api/meetings/{mid}/debate'); assert debated.status_code==200
    assert len(debated.json()['messages'])==7 and len(calls)==7
    asked=client.post(f'/api/meetings/{mid}/ask',json={'agent_id':'finance','question':'What is the downside financial impact?'})
    assert asked.status_code==200 and len(asked.json()['messages'])==9
    assert asked.json()['messages'][-2]['speaker_name']=='Chairperson'
    summarized=client.post(f'/api/meetings/{mid}/summary')
    assert summarized.status_code==200 and summarized.json()['messages'][-1]['speaker_id']=='chief'
    assert summarized.json()['status']=='open' and summarized.json()['decision'] is None
    decided=client.post(f'/api/meetings/{mid}/decision',json={'decision':'Launch controlled pilot'})
    assert decided.json()['status']=='closed'
    assert client.post(f'/api/meetings/{mid}/debate').status_code==409

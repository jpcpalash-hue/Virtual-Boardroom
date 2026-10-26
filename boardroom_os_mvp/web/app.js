(() => {
  'use strict';
  const roster = [
    {id:'chief',name:'Alex Morgan',role:'Chief of Staff',color:'#c4a675',initials:'AM',seat:{x:600,y:312,s:.69},skin:'#bd9376',hair:'#4b4140',coat:'#59676c'},
    {id:'strategy',name:'Victoria Chen',role:'Strategy Director',color:'#7db7de',initials:'VC',seat:{x:390,y:375,s:.72},skin:'#cb9a80',hair:'#202930',coat:'#556f83'},
    {id:'finance',name:'Daniel Reed',role:'Finance Director',color:'#80c8a9',initials:'DR',seat:{x:298,y:490,s:.85},skin:'#b98a68',hair:'#3c3536',coat:'#414d53'},
    {id:'operations',name:'Elena Brooks',role:'Operations Director',color:'#ae9ce4',initials:'EB',seat:{x:177,y:655,s:1.03},skin:'#e1b59c',hair:'#30292b',coat:'#5b5165'},
    {id:'risk',name:'Amara Okafor',role:'Chief Risk Officer',color:'#e0ab86',initials:'AO',seat:{x:812,y:375,s:.72},skin:'#8a5945',hair:'#201c24',coat:'#694e50'},
    {id:'technology',name:'Noah Patel',role:'Technology Director',color:'#89c7cf',initials:'NP',seat:{x:898,y:490,s:.85},skin:'#c38c6e',hair:'#212a32',coat:'#36545b'},
    {id:'devil',name:'Marcus Vale',role:"Devil's Advocate",color:'#ef929b',initials:'MV',seat:{x:1028,y:655,s:1.03},skin:'#d3a27d',hair:'#302a28',coat:'#684d52'},
  ];
  const lookup = Object.fromEntries(roster.map(a=>[a.id,a]));
  const $ = id=>document.getElementById(id);
  const demoMeeting = {id:'demo',title:'Career growth vs financial security',agenda:'Should I prioritize a better-paying role or a higher-growth opportunity?',context:'One option offers more security and near-term compensation. The other could create stronger long-term career upside, with more uncertainty.',participants:['strategy','finance','risk','devil'],messages:[],status:'open',decision:null};
  let meeting = JSON.parse(JSON.stringify(demoMeeting));
  let isDemo = true;
  let selected = 'strategy';
  let active = null;
  let busy = false;
  let demoRound = 0;
  let aiAvailable = false;
  let toastTimer;
  const demoOpening = [
    ['strategy', 'My initial view: prioritize the option that compounds your capabilities and expands future choices. Compare role scope, quality of mentors and ownership over three to five years—not only the first-year salary. I would favor the growth role if its path is credible.'],
    ['finance', 'I would not decide without real numbers. Compare guaranteed take-home pay, signing and relocation costs, debt obligations and a realistic three-year earnings range. A higher salary now can fund optionality; a promised future payoff must be treated as uncertain.'],
    ['risk', 'Both choices carry risk, just in different forms. The secure offer risks slower skill growth; the high-growth offer risks instability and unmet expectations. Identify a worst-case scenario for each, your financial runway and how easily you could switch paths.'],
    ['devil', 'The board is assuming these labels—“secure” and “high growth”—are accurate. What independent evidence supports them? Challenge the job descriptions, speak with former employees and test whether the claimed upside is actually attainable.']
  ];
  const demoDebate = [
    ['strategy', 'Finance is right to demand numbers, but a simple salary comparison undervalues future opportunity. I would build a scenario matrix with skills, network and promotion probability as explicit—but uncertain—inputs.'],
    ['finance', 'Strategy is overweighting upside without proving it. If the growth role has lower guaranteed compensation, the Chairperson should demand a quantified downside and a date by which promised advancement can be validated.'],
    ['devil', 'Both sides are assuming a decision must be final. What about negotiating compensation, asking for a different role scope or setting a six-month review? Reversible experiments may dominate an all-or-nothing choice.']
  ];
  function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
  function line(s,n=32){return s.length>n?s.slice(0,n-1)+'…':s;}
  function hexOpacity(hex){return hex+'55';}
  function makePerson(a){
    const {x,y,s}=a.seat;
    const female = ['strategy','operations','risk'].includes(a.id);
    const hair=female ? `<path d="M-28 -76 Q-31 -116 0 -120 Q32 -113 29 -71 L32 -15 L19 -22 L14 -82Z" fill="${a.hair}"/><path d="M-27 -82 Q-36 -63 -28 -16 L-15 -24 L-14 -68Z" fill="${a.hair}"/>` : `<path d="M-28 -77 Q-34 -110 -6 -111 Q24 -117 30 -91 L26 -80 Q7 -94 -17 -81Z" fill="${a.hair}"/>`;
    return `<g class="board-agent" id="person-${a.id}" role="button" tabindex="0" aria-label="Select ${esc(a.name)}, ${esc(a.role)}" data-agent="${a.id}" transform="translate(${x} ${y}) scale(${s})">
        <ellipse class="avatar-halo" cx="0" cy="-45" rx="53" ry="89" fill="${hexOpacity(a.color)}" filter="url(#activeglow)"/>
        <rect x="-50" y="-56" width="100" height="132" rx="31" fill="#101c27" stroke="#445663" stroke-width="5"/>
        <path d="M-53 38 Q-45 2 -22 2 L-10 11 L12 11 L26 1 Q55 5 58 41 L61 100 L-60 100Z" fill="${a.coat}" stroke="#13242d" stroke-width="3"/>
        <path d="M-20 4 L0 55 L-35 15Z M23 4 L0 55 L37 14Z" fill="#a3afb2" opacity=".33"/>
        <path d="M-13 2 L0 36 L13 2" fill="#f0e6dd"/><path d="M-5 17 L5 17 L9 54 L0 65 L-8 54Z" fill="${a.color}" opacity=".9"/>
        <rect x="-10" y="-16" width="20" height="32" rx="7" fill="${a.skin}"/>
        <ellipse cx="0" cy="-58" rx="27" ry="35" fill="${a.skin}"/>
        ${hair}
        <path d="M-14 -58 Q-10 -62 -5 -58 M5 -58 Q10 -62 15 -58" stroke="#302c29" opacity=".7" stroke-width="2" fill="none"/><path d="M-7 -40 Q0 -36 7 -40" fill="none" stroke="#6a4640" opacity=".6" stroke-width="2"/>
      </g>`;
  }
  function makeTag(a){
    let tx=a.seat.x, ty=a.seat.y-112*a.seat.s;
    if(a.id==='chief')ty=230;
    let w = a.id==='chief'?118: a.id==='operations'?125: a.id==='technology'?120: a.id==='devil'?129:112;
    return `<g class="name-tag" id="tag-${a.id}" data-agent="${a.id}" role="button" tabindex="0" aria-label="Select ${esc(a.role)}"><rect x="${tx-w/2}" y="${ty-17}" width="${w}" height="36" rx="8" fill="#0b1924" stroke="#657682" opacity=".98"/><rect x="${tx-w/2+5}" y="${ty-10}" width="4" height="21" rx="2" fill="${a.color}"/><text x="${tx+3}" y="${ty-2}" text-anchor="middle" fill="#e7eff0" font-size="12" font-weight="700">${esc(a.name)}</text><text x="${tx+3}" y="${ty+12}" text-anchor="middle" fill="#a0b5be" font-size="9">${esc(a.role)}</text></g>`;
  }
  function buildRoom(){
    $('agent-layer').innerHTML=roster.map(makePerson).join('');
    $('name-layer').innerHTML=roster.map(makeTag).join('');
    for(const a of roster){
      for(const id of ['person-'+a.id,'tag-'+a.id]){
        $(id).addEventListener('click',()=>select(a.id));
        $(id).addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select(a.id);}});
      }
    }
  }
  function buildMembers(){
    $('member-list').innerHTML=roster.map(a=>`<button class="member" id="member-${a.id}" data-agent="${a.id}"><span class="member-icon" style="color:${a.color};border-color:${a.color}55">${a.initials}</span><span class="member-desc"><strong>${esc(a.name)}</strong><small>${esc(a.role)}</small></span><span class="member-speaking" id="status-${a.id}"></span></button>`).join('');
    document.querySelectorAll('.member').forEach(b=>b.addEventListener('click',()=>select(b.dataset.agent)));
  }
  function select(agentId){
    if(!lookup[agentId])return;
    selected=agentId;
    for(const a of roster){
      $('person-'+a.id).classList.toggle('selected',a.id===selected);
      $('tag-'+a.id).classList.toggle('selected',a.id===selected);
      $('member-'+a.id).classList.toggle('selected',a.id===selected);
    }
    if(!busy){
      const a=lookup[agentId];
      const recent=[...meeting.messages].reverse().find(m=>m.speaker_id===agentId);
      showSpeech(agentId,recent?.content || `${a.name}, ${a.role}. ${a.id==='chief'?'I will help organize your meeting.':'Click Ask or type a question to hear this advisor’s perspective.'}`,false);
    }
    $('question-input').placeholder=`Chairperson: Ask ${lookup[selected].name} a question…`;
  }
  function showSpeech(agentId,text,speaking=false){
    if(active && lookup[active])$('person-'+active).classList.remove('active');
    active=agentId;
    const agent=lookup[agentId];
    if(agent)$('person-'+agentId).classList.toggle('active',speaking);
    $('speaker-label').textContent=agent?`${agent.name.toUpperCase()} · ${agent.role.toUpperCase()}`:'THE CHAIRPERSON';
    $('speaker-dot').style.background=agent?.color||'#c8ae88';
    $('speech-text').textContent=text;
    $('speech').classList.toggle('active',speaking);
    roster.forEach(a=>{$('status-'+a.id).textContent=speaking&&agentId===a.id?'◖◗':'';});
  }
  function appendMessage(m){
    const agent=lookup[m.speaker_id];
    const avatar=agent?.initials||'C';
    const color=agent?.color||'#e0bc86';
    const e=document.createElement('div');e.className='msg';
    e.innerHTML=`<div class="msg-avatar" style="color:${color};border-color:${color}77;background:${color}17">${avatar}</div><div><div class="msg-top"><span class="msg-name">${esc(agent?.name||'Chairperson')}</span><span class="msg-mode">${esc(m.mode||'note')}</span><span class="msg-time">${new Date(m.created_at||Date.now()).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</span></div><p></p></div>`;
    e.querySelector('p').textContent=m.content;
    $('transcript').appendChild(e);
    $('transcript').scrollTop=$('transcript').scrollHeight;
    $('message-count').textContent=meeting.messages.length;
  }
  function refreshTranscript(){
    $('transcript').innerHTML='';
    if(!meeting.messages.length){$('transcript').innerHTML='<div class="empty-transcript">The room is assembled. Open a discussion to hear independent specialist perspectives.<br/>Select any advisor to inspect their seat.</div>';}
    else meeting.messages.forEach(appendMessage);
    $('message-count').textContent=meeting.messages.length;
  }
  function phase(){
    let count=meeting.messages.filter(m=>m.mode==='debate').length;
    return meeting.status==='closed'?'Closed · Approved':meeting.messages.some(m=>m.mode==='summary')?'Board recommendation':count?'Cross-examination':meeting.messages.length?'Initial assessments':'Opening brief';
  }
  function refresh(){
    $('meeting-title').textContent=meeting.title;
    $('agenda-title').textContent=meeting.agenda;
    $('agenda-context').textContent=meeting.context||'No additional meeting context yet.';
    $('phase-label').textContent=phase();
    $('decision-status').textContent=meeting.status==='closed'?'Chair approved':'Awaiting chair';
    $('svg-title').textContent=line(meeting.title,28);
    $('svg-subtitle').textContent='Independent views · Debate · Chair decision';
    $('session-tag').textContent=isDemo?'●  SCRIPTED DEMO':'●  LIVE MEETING';
    $('meeting-mode').textContent=isDemo?'DEMONSTRATION — PREWRITTEN RESPONSES':'LIVE AI BOARDROOM · FIRST-PERSON VIEW';
    $('round-number').textContent=isDemo?'DEMO SESSION / CHAIR POV':'MEETING '+meeting.id.slice(0,8).toUpperCase();
    $('opening-btn').disabled=busy||meeting.status==='closed'||meeting.messages.length>0;
    $('debate-btn').disabled=busy||meeting.status==='closed'||!meeting.messages.length;
    $('summary-btn').disabled=busy||meeting.status==='closed'||!meeting.messages.length;
    $('decision-btn').disabled=busy||meeting.status==='closed';
    $('question-input').disabled=busy||meeting.status==='closed';
    $('send-question').disabled=busy||meeting.status==='closed';
    $('minutes-btn').disabled=isDemo;
    refreshTranscript();select(selected);
  }
  function notify(message){
    clearTimeout(toastTimer);$('toast').textContent=message;$('toast').style.display='block';toastTimer=setTimeout(()=>{$('toast').style.display='none';},5500);
  }
  function lock(flag){busy=flag;refresh();}
  async function api(path,method='GET',body){
    const response=await fetch(path,{method,headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined});
    if(!response.ok){let err;try{err=await response.json();}catch{}throw new Error(err?.detail||`Request failed (${response.status})`);}
    return await response.json();
  }
  async function showBatch(newMeeting,oldCount){
    const unseen=newMeeting.messages.slice(oldCount);
    meeting=newMeeting;
    $('transcript').innerHTML='';
    meeting.messages.slice(0,oldCount).forEach(appendMessage);
    for(const msg of unseen){
      appendMessage(msg);
      showSpeech(msg.speaker_id,msg.content,true);
      await new Promise(resolve=>setTimeout(resolve,1000));
    }
    if(active&&lookup[active]){$('person-'+active).classList.remove('active');$('speech').classList.remove('active');}
  }
  async function scriptedBatch(items,mode){
    $('transcript').innerHTML='';
    meeting.messages.forEach(appendMessage);
    for(const [speaker,content] of items){
      const m={speaker_id:speaker,speaker_name:lookup[speaker].name,content,mode,created_at:new Date().toISOString()};
      meeting.messages.push(m);
      appendMessage(m);
      showSpeech(speaker,content,true);
      await new Promise(resolve=>setTimeout(resolve,800));
    }
    if(active&&lookup[active]){$('person-'+active).classList.remove('active');$('speech').classList.remove('active');}
  }
  async function doRound(which){
    if(busy)return;
    if(meeting.status!=='open')return notify('This meeting is closed. Start a new one.');
    lock(true);
    try{
      if(isDemo){
        if(which==='opening'&&demoRound===0){demoRound=1;await scriptedBatch(demoOpening,'opening');}
        else if(which==='debate'){demoRound++;await scriptedBatch(demoDebate,'debate');}
        else if(which==='summary'){
          await scriptedBatch([['chief','The demonstration board sees two viable paths. Finance favors protecting near-term flexibility; Strategy favors verified long-term capability growth; Risk requires downside protection. The strongest next step is to compare real offer terms, clarify uncertainty, and only then make a decision. Chairperson, the decision is yours.']],'summary');
        }
        else notify('Opening round already completed. Try debate.');
      }else{
        const oldCount=meeting.messages.length;
        const next=await api(`/api/meetings/${meeting.id}/${which}`,'POST');
        await showBatch(next,oldCount);
      }
    }catch(e){notify(e.message);}finally{lock(false);}
  }
  async function ask(e){
    e.preventDefault();if(busy)return;
    const question=$('question-input').value.trim();if(!question)return;
    if(isDemo)return notify('This is a scripted visual demo, not a live AI conversation. Configure OPENAI_API_KEY and create a live meeting to ask your own questions.');
    lock(true);
    try{
      const oldCount=meeting.messages.length;
      const next=await api(`/api/meetings/${meeting.id}/ask`,'POST',{agent_id:selected,question});
      $('question-input').value='';
      await showBatch(next,oldCount);
    }catch(e){notify(e.message);}finally{lock(false);}
  }
  async function onNewMeeting(e){
    e.preventDefault();
    const form=$('meeting-form');const data=Object.fromEntries(new FormData(form));
    try{
      const newMeeting=await api('/api/meetings','POST',data);
      meeting=newMeeting;isDemo=false;demoRound=0;selected='chief';
      $('meeting-dialog').close();form.reset();refresh();
      showSpeech('chief','Your board is assembled. Start the opening round to hear independent expert analysis.',false);
      if(!aiAvailable)notify('Your meeting was created, but the API key is not configured. Add OPENAI_API_KEY on the server for live AI discussions.');
      else notify('Meeting created. Open the discussion to hear from your board.');
    }catch(error){notify(error.message);}
  }
  async function onDecision(e){
    e.preventDefault(); const data=Object.fromEntries(new FormData($('decision-form')));
    if(isDemo){meeting.decision=data.decision;meeting.status='closed';$('decision-dialog').close();refresh();return notify('Demo resolution recorded only in this browser session. Start a live meeting to persist a decision.');}
    try{meeting=await api(`/api/meetings/${meeting.id}/decision`,'POST',data);$('decision-dialog').close();refresh();notify('Chairperson’s decision approved and saved.');}
    catch(err){notify(err.message);}
  }
  async function openHistory(){
    try{
      const meetings=await api('/api/meetings');
      $('history-list').innerHTML=meetings.length?meetings.map(m=>`<button class="history-row" data-id="${esc(m.id)}"><div><strong>${esc(m.title)}</strong><small>${new Date(m.created_at).toLocaleDateString()} · ${esc(line(m.agenda,55))}</small></div><em>${m.status==='closed'?'DECIDED':'OPEN'}</em></button>`).join(''):'<p>No saved meetings yet. Start your first live meeting.</p>';
      $('history-list').querySelectorAll('button').forEach(b=>b.addEventListener('click',async()=>{try{meeting=await api('/api/meetings/'+encodeURIComponent(b.dataset.id));isDemo=false;selected='chief';$('history-dialog').close();refresh();notify('Previous meeting loaded.');}catch(e){notify(e.message);}}));
      $('history-dialog').showModal();
    }catch(e){notify(e.message);}
  }
  async function checkHealth(){
    try{const h=await api('/api/health');aiAvailable=!!h.live_ai;
      $('connection').classList.toggle('connected',aiAvailable);
      $('connection').innerHTML=`<i></i> ${aiAvailable?'AI READY · '+esc(h.model):'DEMO MODE · API KEY NEEDED'}`;
    }catch{$('connection').innerHTML='<i></i> Offline preview';}
  }
  $('opening-btn').addEventListener('click',()=>doRound('opening'));
  $('debate-btn').addEventListener('click',()=>doRound('debate'));
  $('summary-btn').addEventListener('click',()=>doRound('summary'));
  $('question-form').addEventListener('submit',ask);
  $('meeting-form').addEventListener('submit',onNewMeeting);
  $('decision-form').addEventListener('submit',onDecision);
  $('new-meeting').addEventListener('click',()=>$('meeting-dialog').showModal());
  $('rail-new').addEventListener('click',()=>$('meeting-dialog').showModal());
  $('decision-btn').addEventListener('click',()=>$('decision-dialog').showModal());
  $('history-top').addEventListener('click',openHistory);
  $('rail-history').addEventListener('click',openHistory);
  $('minutes-btn').addEventListener('click',()=>{
    if(isDemo)return notify('Demo has no downloadable minutes.');
    window.location.href=`/api/meetings/${meeting.id}/export`;
  });
  document.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',() => $(b.dataset.close).close()));
  for(const dialog of document.querySelectorAll('dialog'))dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close();});
  buildRoom();buildMembers();refresh();showSpeech('chief','Welcome, Chairperson. This is a scripted visual demonstration. Run the opening discussion to see advisors speak, or create a live AI meeting.',false);checkHealth();
})();

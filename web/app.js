(() => {
const D = window.DATA;
const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const byId = (arr) => Object.fromEntries(arr.map(x => [x.id, x]));
const CE = D.counter_evidence || [], CTX = D.context_lines ?? 2;
const ORG = byId(D.organisations), PART = byId(D.participants), INT = byId(D.interviews), INS = byId(D.insights), OPP = byId(D.opportunities);
const TYPE_LABEL = {target_customer:"Target customer", adjacent_user:"Adjacent user", expert:"Expert"};
const INS_TYPE = {behaviour:"Behaviour", opinion:"Opinion", feature_request:"Feature request", context:"Context"};
const SEV = ["blocker","workaround","irritation","unknown"];
const SEV_LABEL = {blocker:"Blocker", workaround:"Workaround", irritation:"Irritation", unknown:"Impact unknown"};
const state = {status:"all", scope:"in_scope", q:"", sort:"target"};

// ---------- header ----------
$("#title").textContent = D.meta.title;
$("#subtitle").textContent = D.meta.subtitle;
$("#demo-banner").hidden = !D.meta.demo;
const inScope = D.opportunities.filter(o => o.scope === "in_scope");
const followups = D.insights.filter(i => i.needs_followup);
$("#stats").innerHTML = [
  [D.interviews.length, "Interviews"], [D.insights.length, "Insights"],
  [inScope.filter(o => !o.parent_id).length, "Opportunities"],
  [`${D.insights.filter(i => i.verified).length + CE.filter(c => c.verified).length}/${D.insights.length + CE.length}`, "Quotes verified"]
].map(([v,l]) => `<div class="stat"><b>${v}</b><span>${l}</span></div>`).join("");
$("#fu-count").textContent = followups.length;
const pending = D.insights.filter(i => i.mapping && !i.mapping.approved);
const pendingCE = CE.filter(c => !c.approved);
$("#rv-count").textContent = pending.length + pendingCE.length;
const NT = D.interviewed?.target_customer ?? 0;
const warn = [];
if (D.interviews.length < 5) warn.push(`Small sample (${D.interviews.length} interviews): treat signals as directional, not conclusive.`);
if (NT === 0) warn.push("No target customers interviewed yet: all evidence comes from experts or adjacent users.");
$("#warn").innerHTML = warn.map(w => `<div class="banner warnb">${esc(w)}</div>`).join("");

// ---------- helpers ----------
const sevBar = (mix, total) => `<div class="sev" title="${SEV.map(k=>`${SEV_LABEL[k]}: ${mix[k]}`).join(" · ")}">${
  SEV.map(k => mix[k] ? `<i class="${k}" style="width:${mix[k]/total*100}%"></i>` : "").join("")}</div>`;
const legend = () => `<div class="legend">${SEV.map(k=>`<span><i style="background:var(--${k})"></i>${SEV_LABEL[k]}</span>`).join("")}</div>`;
const who = i => { const p = PART[i.participant_id], o = ORG[i.org_id];
  return `<a href="#/customer/${o.id}">${esc(o.pseudonym)}</a> · ${esc(p.role)} <span class="badge ${p.participant_type}">${TYPE_LABEL[p.participant_type]}</span>`; };
const verifiedMark = i => i.verified ? `<span class="ok" title="Quote found word-for-word in the transcript">✓ verified</span>` : `<span class="fail" title="${esc(i.verify_note)}">⚠ not verified</span>`;
const lineRef = i => `<a href="#/interview/${i.interview_id}/${i.lines[0]}-${i.lines[1]}">${i.interview_id} · L${i.lines[0]}${i.lines[1]!==i.lines[0]?"–"+i.lines[1]:""} ↗</a>`;
const KIND = {yes_no:"yes/no question", leading:"leading question"};
function lineHTML(t, n, cls=""){
  if (t === null || t === undefined) return `<div class="tl withheld"><span class="n">⋯</span><span>withheld</span></div>`;
  const m=t.match(/^((?:\[[0-9:]+\]\s*)?[^:]{1,40}):\s(.*)$/); const isInt = m && /interviewer/i.test(m[1]);
  return `<div class="tl ${cls} ${isInt?"int":""}"><span class="n">${n}</span><span>${m?`<span class="spk">${esc(m[1])}:</span> ${esc(m[2])}`:esc(t)}</span></div>`;
}
function contextRows(x){
  const it = INT[x.interview_id]; if(!it) return "";
  const [a,b] = x.lines, asked = x.asked_lines || [];
  const from = Math.max(1, Math.min(a - CTX, ...(asked.length?asked:[a]))), to = Math.min(it.transcript.length, b + CTX);
  const rows = []; for(let n=from;n<=to;n++){ const t=it.transcript[n-1]; if(t==="" ) continue;
    rows.push(lineHTML(t, n, n>=a&&n<=b ? "hl" : (x.weak_question && n===x.weak_question.line ? "flagq" : ""))); }
  return `<div class="transcript ctxbox">${rows.join("")}</div>`;
}
const context = x => `<details class="more"><summary>Show in context</summary>${weakBadge(x)}${contextRows(x)}</details>`;
const weakBadge = x => x.weak_question ? `<div class="weak" title="${esc(x.weak_question.reason)}">⚠ Weaker evidence: answer to a ${KIND[x.weak_question.kind]} (L${x.weak_question.line}) · ${esc(x.weak_question.reason)}</div>` : "";
function evidence(i, showOpp=false, trustMarks=true){
  const o = OPP[i.mapping?.opportunity_id], p = PART[i.participant_id], org = ORG[i.org_id];
  const sev = i.severity && i.severity!=="unknown" ? ` · <span class="sevtxt ${i.severity}">${SEV_LABEL[i.severity]}</span>` : "";
  const marks = [
    i.verified ? `<span class="mk ok" title="Quote found word-for-word in the transcript">✓ Verified</span>` : `<span class="mk fail" title="${esc(i.verify_note)}">⚠ Not verified</span>`,
    trustMarks && i.weak_question ? `<span class="mk weakmk" title="${esc(i.weak_question.reason)}">Weaker evidence</span>` : "",
    i.needs_followup ? `<span class="mk fumk">Follow-up</span>` : ""].join("");
  return `<div class="ev">
    <div class="ev-head"><div class="st">${esc(i.statement)}</div><div class="marks">${marks}</div></div>
    <blockquote>“${esc(i.quote)}”</blockquote>
    <div class="meta"><a href="#/customer/${org.id}">${esc(org.pseudonym)}</a> · ${esc(p.role)} · ${INS_TYPE[i.type]}${sev} · ${lineRef(i)}${showOpp&&o?` · <a href="#/opportunity/${o.id}">${esc(o.title)}</a>`:""}</div>
    <details class="more"><summary>Details</summary>
      ${weakBadge(i)}
      ${i.interpretation_note?`<div class="note"><b>Interpretation:</b> ${esc(i.interpretation_note)}</div>`:""}
      ${i.needs_followup?`<div class="fu"><b>Follow-up:</b> ${esc(i.followup_question)}</div>`:""}
      <div class="note"><b>Who:</b> ${TYPE_LABEL[p.participant_type]} · <b>Research questions:</b> ${(i.research_questions||[]).map(r=>`<span title="${esc(D.research_questions[r])}">${r}</span>`).join(", ")} · ${esc(i.date||"")}</div>
      <div class="lbl2">In context</div>${contextRows(i)}
    </details>
  </div>`;
}

function counter(c, withOpp=false){
  const o = OPP[c.opportunity_id], p = PART[c.participant_id], org = ORG[c.org_id];
  return `<div class="ev against">
    <div class="ev-head"><div class="st">${withOpp&&o?`Against: ${esc(o.title)}`:esc(c.reason)}</div><div class="marks">${c.verified?`<span class="mk ok">✓ Verified</span>`:`<span class="mk fail" title="${esc(c.verify_note)}">⚠ Not verified</span>`}${c.weak_question?`<span class="mk weakmk" title="${esc(c.weak_question.reason)}">Weaker evidence</span>`:""}</div></div>
    <blockquote>“${esc(c.quote)}”</blockquote>
    <div class="meta"><a href="#/customer/${org.id}">${esc(org.pseudonym)}</a> · ${esc(p.role)} · ${lineRef(c)}</div>
    <details class="more"><summary>Details</summary>${withOpp?`<div class="note"><b>Why it counts against:</b> ${esc(c.reason)}</div>`:""}${weakBadge(c)}<div class="lbl2">In context</div>${contextRows(c)}</details>
  </div>`;
}
const guide = html => `<div class="guide">${html}</div>`;
// ---------- views ----------
function viewOpportunities(){
  const cov = Object.entries(D.research_questions).map(([k,label]) => {
    const c = D.rq_coverage[k] || {count:0,target_customers:0}; const gap = c.target_customers < 2;
    return `<div class="${gap?"gap":""}"><b>${k}</b><p>${esc(label)}</p><small>${c.count} insights · ${c.target_customers} target customer${c.target_customers===1?"":"s"}${gap?" · needs more evidence":""}</small></div>`;
  }).join("");
  const sorters = {
    target:(a,b)=>b.signals.unique_target_customers-a.signals.unique_target_customers||b.signals.total_mentions-a.signals.total_mentions,
    severity:(a,b)=>(b.signals.severity_mix.blocker*2+b.signals.severity_mix.workaround)-(a.signals.severity_mix.blocker*2+a.signals.severity_mix.workaround),
    mentions:(a,b)=>b.signals.total_mentions-a.signals.total_mentions,
    recent:(a,b)=>String(b.signals.latest_evidence).localeCompare(String(a.signals.latest_evidence)),
  };
  const match = o => (state.status==="all"||o.status===state.status) && o.scope===state.scope && (!state.q || (o.title+" "+(o.summary||"")).toLowerCase().includes(state.q.toLowerCase()));
  const tops = D.opportunities.filter(o => !o.parent_id && (match(o) || o.children.some(c=>match(OPP[c])))).sort(sorters[state.sort]);
  const row = (o, child) => { const s=o.signals; const others = s.adjacent_users+s.experts;
    return `<div class="row ${child?"child":""}" data-go="#/opportunity/${o.id}">
      <div class="title">${esc(o.title)}</div>
      <div class="num"><span class="big">${s.unique_target_customers}</span><span class="other">/${NT}</span></div>
      <div class="num hide-sm" title="${s.total_mentions} insights">${s.interviews}</div>
      <div>${s.total_mentions?sevBar(s.severity_mix,s.total_mentions):""}</div>
      <div class="num hide-sm ${o.counter_evidence.length?"againstn":"other"}" title="Verified quotes that count against this">${o.counter_evidence.length||"–"}</div>
      <div class="hide-sm" style="text-align:right"><span class="badge ${o.status}">${o.status[0].toUpperCase()+o.status.slice(1)}</span></div>
    </div>`; };
  const rows = tops.map(o => row(o,false) + o.children.map(c=>OPP[c]).filter(match).sort(sorters[state.sort]).map(c=>row(c,true)).join("")).join("");
  $("#view").innerHTML = `
    ${guide(`<b>Step 2 · Decide.</b> The problems customers raised, with how many people and how strong the evidence is. Open one to see the quotes for and against.`)}
    <div class="controls">
      ${["all","open","exploring","addressed"].map(s=>`<button class="chip ${state.status===s?"on":""}" data-status="${s}">${s[0].toUpperCase()+s.slice(1)}</button>`).join("")}
      <span style="width:8px"></span>
      <button class="chip ${state.scope==="in_scope"?"on":""}" data-scope="in_scope">In scope</button>
      <button class="chip ${state.scope==="parking_lot"?"on":""}" data-scope="parking_lot">Parking lot (${D.opportunities.filter(o=>o.scope==="parking_lot").length})</button>
      <select id="sort" title="Sort">
        <option value="target">Sort: target customers</option><option value="severity">Sort: severity</option>
        <option value="mentions">Sort: mentions</option><option value="recent">Sort: most recent</option></select>
      <input class="search" id="q" placeholder="Search opportunities…" value="${esc(state.q)}">
    </div>
    <div class="table">
      <div class="row head"><div>Opportunity</div><div class="num" title="Unique target customers">Target cust.</div><div class="num hide-sm" title="Interviews where this came up">Interviews</div><div>Severity</div><div class="num hide-sm" title="Verified quotes that count against this opportunity">Against</div><div class="hide-sm" style="text-align:right">Status</div></div>
      ${rows || `<div class="row"><div class="other">No opportunities match.</div></div>`}
    </div>${legend()}
    <details class="more" style="margin-top:18px"><summary>Research question coverage</summary><div class="rq" style="margin-top:10px">${cov}</div></details>
    <p class="other">No single priority score by design. Signals come from the transcripts; market fit, company fit and the final decision are yours.</p>`;
  $("#sort").value = state.sort;
  document.querySelectorAll("[data-status]").forEach(b=>b.onclick=()=>{state.status=b.dataset.status;viewOpportunities();});
  document.querySelectorAll("[data-scope]").forEach(b=>b.onclick=()=>{state.scope=b.dataset.scope;viewOpportunities();});
  $("#sort").onchange = e => {state.sort=e.target.value;viewOpportunities();};
  const q=$("#q"); q.oninput = e => {state.q=e.target.value;viewOpportunities();const n=$("#q");n.focus();n.setSelectionRange(n.value.length,n.value.length);};
}

function viewOpportunity(id){
  const o = OPP[id]; if(!o) return notFound();
  const s = o.signals, parent = o.parent_id && OPP[o.parent_id];
  const ev = s.insight_ids.map(i=>INS[i]);
  const groups = ["target_customer","adjacent_user","expert"].map(t => {
    const items = ev.filter(i => PART[i.participant_id].participant_type===t);
    return items.length ? `<div class="group"><h3>${TYPE_LABEL[t]}s · ${items.length}</h3>${items.map(i=>evidence(i,false,false)).join("")}</div>` : "";
  }).join("");
  const field = (label,v) => `<div><div class="lbl">${label}</div>${v?esc(v):`<span class="empty">Not assessed yet</span>`}</div>`;
  $("#view").innerHTML = `
    <a class="back" href="#/opportunities">← All opportunities</a>
    ${parent?`<div class="crumb">Part of <a href="#/opportunity/${parent.id}">${esc(parent.title)}</a></div>`:""}
    <h2>${esc(o.title)}</h2>
    <span class="badge ${o.status}">${o.status[0].toUpperCase()+o.status.slice(1)}</span> ${o.scope==="parking_lot"?`<span class="badge">Parking lot</span>`:""}
    <div class="kpis">
      <div class="kpi"><b>${s.unique_target_customers}<small class="other">/${NT}</small></b><span>Target customers</span></div>
      <div class="kpi"><b>${s.adjacent_users}</b><span>Adjacent users</span></div>
      <div class="kpi"><b>${s.experts}</b><span>Experts</span></div>
      <div class="kpi"><b>${s.interviews}<small class="other">/${D.interviews.length}</small></b><span>Interviews</span></div>
      <div class="kpi"><b>${s.total_mentions}</b><span>Insights</span></div>
      <div class="kpi"><b>${Math.round(s.behaviour_ratio*100)}%</b><span>Behaviour evidence</span></div>
      <div class="kpi"><b class="${o.counter_evidence.length?"againstn":""}">${o.counter_evidence.length}</b><span>Against</span></div>
      <div class="kpi" style="min-width:160px"><div style="margin:8px 0 6px">${s.total_mentions?sevBar(s.severity_mix,s.total_mentions):""}</div><span>${SEV.filter(k=>s.severity_mix[k]).map(k=>`${s.severity_mix[k]} ${SEV_LABEL[k].toLowerCase()}`).join(" · ")}</span></div>
    </div>
    ${o.summary?`<div class="panel"><div class="lbl">AI synthesis · from ${s.total_mentions} insights below only</div>${esc(o.summary)}</div>`:""}
    ${o.children.length?`<h3>Sub-opportunities</h3>${o.children.map(c=>`<div class="mini" data-go="#/opportunity/${c}"><b>${esc(OPP[c].title)}</b> <span class="other">· ${OPP[c].signals.unique_target_customers} target customers · ${OPP[c].signals.total_mentions} insights</span></div>`).join("")}`:""}
    <h3>Your assessment</h3>
    <div class="assess">${field("Market factor",o.market_factor)}${field("Company factor",o.company_factor)}${field("Decision rationale",o.decision_rationale)}</div>
    ${groups || `<p class="other">No evidence attached.</p>`}
    <h3>Evidence against · ${o.counter_evidence.length}</h3>
    ${o.counter_evidence.length ? o.counter_evidence.map(c=>counter(CE.find(x=>x.id===c))).join("")
      : `<p class="other">No counter-evidence found in ${D.interviews.length} interviews. Absence of evidence is not proof: ask “who would say this isn’t a problem?”</p>`}`;
}

function viewCustomers(){
  $("#view").innerHTML = `<div class="cards">${D.organisations.map(o => {
    const ps = D.participants.filter(p=>p.org_id===o.id), ins = D.insights.filter(i=>i.org_id===o.id);
    const opps = new Set(ins.map(i=>i.mapping?.opportunity_id).filter(Boolean));
    return `<div class="card" data-go="#/customer/${o.id}">
      <h4>${esc(o.pseudonym)}</h4><p>${esc(o.sector)} · ${esc(o.country)} · ${esc(o.size_band)}</p>
      <div style="margin-top:8px">${ps.map(p=>`<span class="badge ${p.participant_type}">${TYPE_LABEL[p.participant_type]}</span>`).join(" ")} ${o.fits_icp?`<span class="badge">Fits ICP</span>`:""}</div>
      <div class="row2"><span><b>${D.interviews.filter(i=>i.org_id===o.id).length}</b> interviews</span><span><b>${ins.length}</b> insights</span><span><b>${opps.size}</b> opportunities</span></div>
    </div>`; }).join("")}</div>`;
}

function viewCustomer(id){
  const o = ORG[id]; if(!o) return notFound();
  const ps = D.participants.filter(p=>p.org_id===id), ints = D.interviews.filter(i=>i.org_id===id), ins = D.insights.filter(i=>i.org_id===id);
  const oppCount = {}; ins.forEach(i=>{const k=i.mapping?.opportunity_id; if(k) oppCount[k]=(oppCount[k]||0)+1;});
  $("#view").innerHTML = `
    <a class="back" href="#/customers">← All customers</a>
    <h2>${esc(o.pseudonym)}</h2>
    <h3>Profile <span class="other" style="text-transform:none;letter-spacing:0">(only facts stated in interviews · source ${esc(o.source)})</span></h3>
    <dl class="facts"><dt>Type</dt><dd>${esc(o.org_type)}</dd><dt>Sector</dt><dd>${esc(o.sector)}</dd><dt>Country</dt><dd>${esc(o.country)}</dd><dt>Size</dt><dd>${esc(o.size_band)}</dd><dt>Fits ICP</dt><dd>${o.fits_icp?"Yes":"No"}</dd></dl>
    <h3>People interviewed</h3>
    ${ps.map(p=>`<div class="ev"><div class="st">${esc(p.role)} <span class="badge ${p.participant_type}">${TYPE_LABEL[p.participant_type]}</span></div>
      <div class="note"><b>Current tools:</b> ${p.current_tools.length?p.current_tools.map(esc).join(", "):"not mentioned"}</div>
      ${p.notes?.length?`<ul class="list note">${p.notes.map(n=>`<li>${esc(n)}</li>`).join("")}</ul>`:""}</div>`).join("")}
    <h3>Opportunities they raised</h3>
    ${Object.entries(oppCount).sort((a,b)=>b[1]-a[1]).map(([k,n])=>`<div class="mini" data-go="#/opportunity/${k}"><b>${esc(OPP[k]?.title||k)}</b> <span class="other">· ${n} insight${n>1?"s":""}</span></div>`).join("")}
    <h3>Interviews</h3>
    ${ints.map(i=>`<div class="mini" data-go="#/interview/${i.id}"><b>${i.id}</b> · ${esc(i.date)} <span class="other">· “${esc(i.memorable_quote?.text||"")}”</span></div>`).join("")}`;
}

function viewInterviews(){
  $("#view").innerHTML = guide(`Look up any interview: its insights, the full transcript and the snapshot.`) + `<div class="table">
    <div class="row head" style="grid-template-columns:90px 100px minmax(0,1fr) 80px 80px 90px 90px"><div>ID</div><div>Date</div><div>Participant</div><div class="num">Insights</div><div class="num">Verified</div><div class="num" title="Share of what the participant said that approved insights use">Coverage</div><div class="num" title="Interviewer questions that were yes/no or leading">Flagged Qs</div></div>
    ${D.interviews.map(i=>{const ins=D.insights.filter(x=>x.interview_id===i.id), p=PART[i.participant_id];
      return `<div class="row" style="grid-template-columns:90px 100px minmax(0,1fr) 80px 80px 90px 90px" data-go="#/interview/${i.id}"><div class="title">${i.id}</div><div>${esc(i.date)}</div><div>${esc(ORG[i.org_id].pseudonym)} · ${esc(p.role)} <span class="badge ${p.participant_type}">${TYPE_LABEL[p.participant_type]}</span></div><div class="num">${ins.length}</div><div class="num ${ins.every(x=>x.verified)?"ok":"fail"}">${ins.filter(x=>x.verified).length}/${ins.length}</div><div class="num">${Math.round((i.coverage?.pct||0)*100)}%</div><div class="num">${(i.question_flags||[]).length}</div></div>`;}).join("")}
  </div>`;
}

function viewInterview(id, hl){
  const it = INT[id]; if(!it) return notFound();
  const p = PART[it.participant_id], ins = D.insights.filter(i=>i.interview_id===id);
  const qlines = new Set(); ins.forEach(i=>{for(let n=i.lines[0];n<=i.lines[1];n++) qlines.add(n);});
  let [ha,hb] = (hl||"").split("-").map(Number); if(ha && !hb) hb=ha;
  const tab = hl ? "transcript" : (state.itab || "insights");
  const cov = it.coverage || {pct:0, uncovered:[]};
  const gap = new Set(); cov.uncovered.forEach(g=>{ for(let n=g.start;n<=g.end;n++){ const t=it.transcript[n-1]; if(t && !/^(\[[0-9:]+\]\s*)?interviewer/i.test(t)) gap.add(n); } });
  const flagAt = {}; (it.question_flags||[]).forEach(f=>(flagAt[f.line] ||= []).push(f));
  const nWeak = ins.filter(i=>i.weak_question).length, nFlags = (it.question_flags||[]).length;
  const tl = it.transcript.map((t,k)=>{const n=k+1;
    if (t === null) return (k>0 && it.transcript[k-1]===null) ? "" : `<div class="tl withheld"><span class="n">⋯</span><span>lines withheld in public version</span></div>`;
    if (t === "") return "";
    const m=t.match(/^((?:\[[0-9:]+\]\s*)?[^:]{1,40}):\s(.*)$/);
    const isInt = m && /interviewer/i.test(m[1]); const fl = flagAt[n];
    return `<div class="tl ${ha&&n>=ha&&n<=hb?"hl":qlines.has(n)?"q":gap.has(n)?"gap":""} ${isInt?"int":""} ${fl?"flagq":""}" id="L${n}"><span class="n">${n}</span><span>${m?`<span class="spk">${esc(m[1])}:</span> ${esc(m[2])}`:`<b>${esc(t)}</b>`}${fl?`<span class="qflag" title="${esc(fl.map(f=>f.reason).join("; "))}">${fl.map(f=>KIND[f.kind]).join(", ")}</span>`:""}</span></div>`;}).join("");
  const trust = `<div class="trust">
    <div><b>${ins.filter(i=>i.verified).length}/${ins.length}</b><span>quotes verified</span></div>
    <div><b>${Math.round(cov.pct*100)}%</b><span>of what they said is used</span></div>
    <div><b>${cov.uncovered.length}</b><span>unused stretches to check</span></div>
    <div><b>${nWeak}</b><span>insights from yes/no or leading questions</span></div>
  </div>`;
  const snapshot = `<div class="panel"><div class="lbl">Memorable quote · L${it.memorable_quote.lines[0]}</div><i>“${esc(it.memorable_quote.text)}”</i></div>
      <h3>Their story</h3><ul class="list">${(it.story||[]).map(s=>`<li>${esc(s)}</li>`).join("")}</ul>
      ${it.interesting?.length?`<h3>Interesting, not yet an opportunity</h3><ul class="list">${it.interesting.map(s=>`<li>${esc(s)}</li>`).join("")}</ul>`:""}`;
  const legendT = `<div class="tlegend"><span><i class="lq"></i>used in an insight</span><span><i class="lg"></i>not used by any insight</span><span><i class="lf"></i>yes/no or leading question (${nFlags})</span>
      <label><input type="checkbox" id="onlygap"> Show only unused lines and flagged questions</label></div>`;
  const body = {
    insights: ins.map(i=>evidence(i,true)).join("") || `<p class="other">No insights yet.</p>`,
    transcript: legendT + `<div class="transcript full" id="tr">${tl}</div>`,
    snapshot };
  $("#view").innerHTML = `
    <a class="back" href="#/interviews">← All interviews</a>
    <h2>${id} · ${esc(ORG[it.org_id].pseudonym)}</h2>
    <p class="sub">${esc(p.role)} · ${TYPE_LABEL[p.participant_type]} · ${esc(it.date)}</p>
    ${trust}
    <div class="itabs">${[["insights",`Insights (${ins.length})`],["transcript","Transcript"],["snapshot","Snapshot"]].map(([k,l])=>`<button class="itab ${tab===k?"on":""}" data-itab="${k}">${l}</button>`).join("")}</div>
    <div id="ibody">${body[tab]}</div>`;
  document.querySelectorAll("[data-itab]").forEach(b=>b.onclick=()=>{ state.itab=b.dataset.itab; if(hl) location.hash="#/interview/"+id; else viewInterview(id); });
  const og=$("#onlygap"); if(og) og.onchange = e => $("#tr").classList.toggle("onlygap", e.target.checked);
  if(ha){ const el=document.getElementById("L"+ha); if(el) el.scrollIntoView({block:"center"}); }
}

function viewFollowups(){
  const byP = {}; followups.forEach(i=>(byP[i.participant_id] ||= []).push(i));
  $("#view").innerHTML = `<p class="other" style="margin-top:0">Questions to ask next time: gaps where a request had no clear “why”, or a hypothesis needs checking with target customers.</p>` +
    (Object.entries(byP).map(([pid,list])=>`<h3>${esc(ORG[PART[pid].org_id].pseudonym)} · ${esc(PART[pid].role)}</h3>${list.map(i=>`<div class="ev"><div class="fu" style="margin-top:0">${esc(i.followup_question)}</div><div class="note">From: “${esc(i.quote)}” · ${lineRef(i)}</div></div>`).join("")}`).join("") || `<p class="other">No open follow-ups.</p>`);
}
function viewReview(){
  const ACT = {attach:"Add to", create_sub:"New sub-problem", create_top:"New problem", parking_lot:"Parking lot"};
  const ids = [...new Set([...pending.map(i=>i.interview_id), ...pendingCE.map(c=>c.interview_id)])];
  const block = iid => {
    const it = INT[iid], list = pending.filter(i=>i.interview_id===iid), ces = pendingCE.filter(c=>c.interview_id===iid);
    const groups = {}; list.forEach(i=>{ const m=i.mapping; const k = m.opportunity_id && OPP[m.opportunity_id] ? "E:"+m.opportunity_id : "N:"+(m.proposed_title||""); (groups[k] ||= []).push(i); });
    const cards = Object.values(groups).sort((a,b)=>b.length-a.length).map(items=>{
      const m=items[0].mapping, o=OPP[m.opportunity_id];
      const title = o ? `<a href="#/opportunity/${o.id}">${esc(o.title)}</a>` : esc(m.proposed_title||"");
      return `<div class="propgroup"><div class="proptitle"><span class="other">${ACT[m.action]||m.action}:</span> <b>${title}</b></div>
        ${items.map(i=>evidence(i).replace('<details class="more"><summary>Details</summary>', `<details class="more"><summary>Details</summary><div class="note"><b>${i.id} · why this group (${i.mapping.confidence} confidence):</b> ${esc(i.mapping.reason)}</div>`).replace('<div class="marks">', `<div class="marks">${i.mapping.confidence!=="high"?`<span class="mk weakmk" title="${esc(i.mapping.reason)}">Check grouping</span>`:""}`)).join("")}</div>`;
    }).join("");
    const cov = it.coverage || {pct:0, uncovered:[]};
    const unused = cov.uncovered.map(g=>{ const rows=[]; for(let n=g.start;n<=g.end;n++){ const t=it.transcript[n-1]; if(t) rows.push(lineHTML(t,n)); }
      return `<div class="transcript ctxbox gapbox">${rows.join("")}</div>`; }).join("");
    const nWeak = list.filter(i=>i.weak_question).length;
    return `<section class="rvblock">
      <h2>${iid} · ${esc(ORG[it.org_id].pseudonym)}</h2>
      <div class="trust">
        <div><b>${list.length}</b><span>insights to review</span></div>
        <div><b>${list.filter(i=>i.verified).length}/${list.length}</b><span>quotes verified</span></div>
        <div><b>${nWeak}</b><span>from yes/no or leading questions</span></div>
        <div><b>${Math.round(cov.pct*100)}%</b><span>of what they said is used</span></div>
      </div>
      <h3>a · Check each insight</h3>
      <p class="other">Quotes are already checked word for word, so judge the meaning: is this what the customer meant? Insights marked <span class="mk weakmk">Weaker evidence</span> answered a yes/no or leading question.</p>
      ${cards}
      ${ces.length?`<h3>b · Evidence against</h3><p class="other">Quotes where the customer says a problem doesn't apply to them. Approve only if that's what they meant.</p>${ces.map(c=>counter(c,true)).join("")}`:""}
      <h3>${ces.length?"c":"b"} · What the AI didn't use · ${cov.uncovered.length} part${cov.uncovered.length===1?"":"s"}</h3>
      <p class="other">Read these instead of the whole transcript. Anything important here that the AI missed?</p>
      ${unused || `<p class="other">The AI used everything the participant said.</p>`}
    </section>`;
  };
  $("#view").innerHTML = guide(`<b>Step 1 · Review.</b> The AI has proposed insights from new interviews. Check them, look at what it left out, then tell Claude what to approve or reject. Nothing counts until you approve it.`)
    + (ids.map(block).join("") || `<div class="panel">✓ All caught up: nothing waiting for review. See <a href="#/opportunities">Step 2 · Opportunities</a>.</div>`);
}
function viewChangelog(){ $("#view").innerHTML = `<pre class="log">${esc(D.changelog||"No changes yet.")}</pre>`; }
function notFound(){ $("#view").innerHTML = `<p>Not found. <a href="#/opportunities">Back</a></p>`; }

// ---------- router ----------
function route(){
  const [, page="review", id, extra] = (location.hash || "#/review").split("/");
  const tab = {opportunity:"opportunities", customer:"customers", interview:"interviews"}[page] || page;
  document.querySelectorAll("#tabs a").forEach(a=>a.classList.toggle("active", a.dataset.tab===tab));
  const mm=$("#moremenu"); if(mm){ mm.open=false; mm.classList.toggle("active", ["customers","followups","changelog"].includes(tab)); }
  ({opportunities:viewOpportunities, opportunity:()=>viewOpportunity(id), customers:viewCustomers, customer:()=>viewCustomer(id),
    interviews:viewInterviews, interview:()=>viewInterview(id, extra), followups:viewFollowups, review:viewReview, changelog:viewChangelog}[page] || notFound)();
  if(page!=="interview" || !extra) window.scrollTo(0,0);
}
document.addEventListener("click", e => { const g = e.target.closest("[data-go]"); if(g && !e.target.closest("a")) location.hash = g.dataset.go; });
window.addEventListener("hashchange", route); route();
})();

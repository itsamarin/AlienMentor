let state;
let lastOutcome = null;
let previewMode = false;
let selectedGraphConcept = null;
const $ = (id) => document.getElementById(id);
const safe = (value) => String(value ?? "").replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));

async function api(url, options) {
  const response = await fetch(url, {headers:{"Content-Type":"application/json"}, ...options});
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || "Something went wrong");
  return body;
}

function render() {
  const modeLabel = state.modeMessage || (state.mode === "neo4j" ? "Neo4j graph connected" : "Offline demo · local progress");
  $("mode-label").textContent = modeLabel;
  document.querySelector(".live-dot")?.classList.toggle("offline", state.mode !== "neo4j");
  $("concept-count").textContent = state.concepts.length;
  $("topic-count").textContent = new Set(state.concepts.map(c=>c.domain)).size;
  $("goal").innerHTML = state.goals.map(g => `<option value="${safe(g.id)}" ${g.id===state.goalId?"selected":""}>${safe(g.name)}</option>`).join("");
  $("level").value = state.level;
  $("minutes").value = state.minutes;
  renderPlan(state.plan);
  renderProgress(state);
  renderGraph(state);
}

function renderPlan(plan) {
  const c = plan.concept;
  const mastery = plan.mastery === null ? "Not assessed" : `${Math.round(plan.mastery*100)}% observed average`;
  const coachLabel = plan.coachSource === "openai" ? "AI generated" : "Curated fallback";
  const prerequisites = (plan.prerequisiteStatus || []).length
    ? `<div class="prerequisite-block"><b>Prerequisites</b>${plan.prerequisiteStatus.map(item=>`<span class="prereq-status ${safe(item.status)}"><i></i>${safe(item.name)} · ${item.status==="mastered"?`${Math.round(item.observedAverage*100)}% observed`:item.status==="review"?"review needed":item.status==="passed"?"latest answer correct":"not assessed"}</span>`).join("")}</div>`
    : `<div class="prerequisite-block"><b>Prerequisites</b><span class="prereq-status mastered"><i></i>Foundation concept · no earlier concepts required</span></div>`;
  $("plan-content").innerHTML = `
    ${lastOutcome ? `<div class="last-outcome ${lastOutcome.correct ? "success" : "review"}" role="status"><span class="outcome-icon">${lastOutcome.correct ? "✓" : "↻"}</span><span><b>Answer saved · ${lastOutcome.correct ? "Correct" : "Needs review"}</b><small>${safe(lastOutcome.feedback)}</small></span></div>` : ""}
    <div class="concept-row"><div class="concept-icon">✳</div><div><div class="concept-domain">${safe(c.domain)} · ${safe(c.level <= 2 ? "Foundation" : c.level <= 4 ? "Core" : "Advanced")}</div><h3 class="concept-title">${safe(c.name)}</h3><p class="description">${safe(plan.lesson || c.description)}</p></div></div>
    <p class="coach-source"><span class="source-badge ${plan.coachSource === "openai" ? "generated" : "curated"}">${coachLabel}</span>${safe(plan.coachNotice || "")}</p>
    <div class="plan-meta"><span class="pill time-pill">◷ ${plan.minutes} min focus</span><span class="pill">Observed result: ${mastery}</span><span class="pill estimate-pill">Estimated mastery: ${Math.round(plan.estimatedMastery*100)}%</span></div>
    <div class="why-heading">Why this is next</div><ul class="why">${plan.reasons.map(r=>`<li>${safe(r)}</li>`).join("")}</ul>
    ${prerequisites}
    ${c.resource?.url ? `<a class="resource-link" href="${safe(c.resource.url)}" target="_blank" rel="noreferrer">Read ${safe(c.resource.title)} ↗</a>` : ""}
    <div class="practice"><div class="practice-head"><strong>Quick practice</strong><span>One question · instant check</span></div><p class="question">${safe(plan.question.prompt)}</p><div class="answers">${plan.question.options.map(o=>`<button class="answer" data-answer="${safe(o)}">${safe(o)}</button>`).join("")}</div><p class="feedback" id="feedback" hidden></p></div>`;
  document.querySelectorAll(".answer").forEach(button=>button.addEventListener("click",()=>submitAnswer(c.id, button.dataset.answer)));
}

function renderProgress(data) {
  const results = data.results;
  const current = data.plan;
  const metrics = current.progress;
  const observed = current.mastery === null ? "—" : `${Math.round(current.mastery*100)}%`;
  const count = results.length;
  const correct = results.filter(r=>r.correct).length;
  $("progress-content").innerHTML = `
    <div class="progress-summary"><div><strong>${metrics.goalPathCompleted}/${metrics.goalPathTotal}</strong><span>goal path concepts mastered</span></div><div><strong>${metrics.conceptsTried}</strong><span>concepts with attempts</span></div><div><strong>${metrics.overallAccuracy===null?"—":`${metrics.overallAccuracy}%`}</strong><span>observed answer accuracy</span></div><div><strong>${metrics.currentStreakDays}</strong><span>day learning streak</span></div></div>
    <div class="goal-progress"><span>Observed goal-path progress</span><b>${metrics.goalPathPercent}%</b><div class="bar"><i style="width:${metrics.goalPathPercent}%"></i></div></div>
    <div class="signal-card estimate-card"><div class="signal-title">Estimated mastery <span>MODEL ESTIMATE</span></div><div class="signal-value">${Math.round(current.estimatedMastery*100)}%</div><div class="signal-caption">${safe(current.estimatedMasteryMethod)} This estimate is not an assessment score.</div><div class="bar"><i style="width:${Math.round(current.estimatedMastery*100)}%"></i></div></div>
    <div class="signal-card observed-card"><div class="signal-title">Observed assessment average <span>RECORDED</span></div><div class="signal-value">${observed}</div><div class="signal-caption">${current.mastery===null?"No recorded assessment for this concept yet.":`Based on ${results.filter(r=>r.conceptId===current.concept.id).length} saved attempt(s) for this concept.`}</div></div>
    <div class="observed-list"><h3>Recent answers <span class="tag">Observed</span></h3>${count?`<p class="activity-summary">${count} saved ${count===1?"answer":"answers"} · ${correct} correct overall</p>${results.slice(-4).reverse().map(r=>`<div class="result-row"><span>${safe(data.concepts.find(c=>c.id===r.conceptId)?.name || r.conceptId)}</span><b class="result-${r.correct?"correct":"review"}">${r.correct?"Correct":"Review"} · ${Math.round(r.score*100)}%</b></div>`).join("")}`:`<p class="empty-result">No practice answers saved yet. Complete the quick practice to record your first result.</p>`}</div>
    <div class="coach-note"><div class="signal-title">Coach recommendation</div><p>${safe(current.concept.name)} was selected from the graph prerequisites and your recorded results. A recommendation is separate from an assessment result.</p></div>`;
}

function renderGraph(data) {
  const svg = $("graph"), allConcepts = data.concepts;
  const recommended = data.plan.concept;
  // Show a compact two-hop neighborhood so the graph reveals course layers,
  // not just the selected concept's immediate links.
  const visibleIds = new Set([recommended.id]);
  let frontier = new Set([recommended.id]);
  for (let depth = 0; depth < 2; depth++) {
    const next = new Set();
    for (const concept of allConcepts) {
      const prerequisites = concept.prerequisites || [];
      if (frontier.has(concept.id)) {
        prerequisites.forEach(id => next.add(id));
      }
      if (prerequisites.some(id => frontier.has(id))) next.add(concept.id);
    }
    next.forEach(id => visibleIds.add(id));
    frontier = next;
  }
  const concepts = allConcepts.filter(concept => visibleIds.has(concept.id));
  const preferred = ["Python","Data science","Neo4j","Cypher","GraphRAG","AI agents","German language","Thai dance","Thai boxing"];
  const groups = [...preferred.filter(domain=>concepts.some(concept=>concept.domain===domain)), ...new Set(concepts.map(concept=>concept.domain).filter(domain=>!preferred.includes(domain)))];
  const xFor = i => groups.length === 1 ? 500 : 55+i*(890/(groups.length-1));
  const byId = Object.fromEntries(allConcepts.map(c=>[c.id,c]));
  const focused = new Set([data.plan.concept.id, ...(data.plan.concept.prerequisites||[])]);
  const scores = Object.fromEntries(allConcepts.map(c=>{
    const items=data.results.filter(r=>r.conceptId===c.id);
    return [c.id,items.length?items.reduce((total,r)=>total+Number(r.score),0)/items.length:null];
  }));
  const latest=Object.fromEntries(data.results.map(result=>[result.conceptId,result]));
  const grouped = Object.fromEntries(groups.map(g=>[g,concepts.filter(c=>c.domain===g)]));
  const layoutHeight = Math.max(410, 100 + Math.max(0, ...groups.map(g=>grouped[g].length))*38);
  svg.setAttribute("viewBox", `0 0 1000 ${layoutHeight}`);
  const points={};
  groups.forEach((g,gi)=>grouped[g].forEach((c,ci)=>{
    const n=grouped[g].length;
    points[c.id]={x:xFor(gi),y:54+(ci+1)*((layoutHeight-100)/(n+1))};
  }));
  let html=`<defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#68829a"/></marker><marker id="arrow-active" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#63e6cd"/></marker></defs>`;
  html += groups.map((g,i)=>`<text x="${xFor(i)}" y="22" text-anchor="middle" font-size="10" font-family="Avenir Next, Segoe UI, sans-serif" font-weight="700">${safe(g.toUpperCase())}</text>`).join("");
  for(const c of concepts) for(const pre of c.prerequisites||[]) if(points[pre]&&points[c.id]){
    const a=points[pre], b=points[c.id], sx=a.x+38, sy=a.y, ex=b.x-39, ey=b.y;
    const active=focused.has(pre)&&focused.has(c.id);
    html+=`<path class="edge ${active?"active":"muted"}" d="M${sx},${sy} C${sx+22},${sy} ${ex-22},${ey} ${ex},${ey}"/>`;
  }
  concepts.forEach(c=>{
    const p=points[c.id],recommended=c.id===data.plan.concept.id,isFocused=focused.has(c.id),score=scores[c.id];
    const label=c.name.length>16?c.name.slice(0,15)+"…":c.name;
    const progressClass=score===null?"unassessed":score>=.7?"mastered":latest[c.id]?.correct?"passed":"review";
    const progressLabel=progressClass==="mastered"?"mastered by assessment average":progressClass==="passed"?"latest answer correct":progressClass==="review"?"review needed":"not assessed";
    html+=`<g class="node ${recommended?"selected":""} ${isFocused?"focused":"muted"} ${progressClass}" transform="translate(${p.x} ${p.y})" tabindex="0" role="button" aria-label="${safe(c.name)} · ${progressLabel}" aria-pressed="${selectedGraphConcept===c.id}" data-concept-id="${safe(c.id)}"><title>${safe(c.name)} · ${progressLabel}</title><circle r="8"/><text y="23">${safe(label)}</text></g>`;
  });
  svg.innerHTML=html;
  $("graph-mobile").innerHTML=allConcepts.map(c=>{
    const score=scores[c.id], progress=score===null?"Not assessed":score>=.7?`Mastered · ${Math.round(score*100)}%`:latest[c.id]?.correct?`Latest answer correct · ${Math.round(score*100)}% avg`:`Review · ${Math.round(score*100)}%`;
    return `<button class="mobile-concept ${c.id===data.plan.concept.id?"recommended":""}" data-concept-id="${safe(c.id)}"><span>${safe(c.name)}</span><small>${safe(c.domain)} · ${progress}</small></button>`;
  }).join("");
  document.querySelectorAll("[data-concept-id]").forEach(node=>{
    node.addEventListener("click",()=>renderNodeDetail(data,node.dataset.conceptId));
    node.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();renderNodeDetail(data,node.dataset.conceptId)}});
  });
  $("graph-count").textContent=`Nearby graph: ${concepts.length} of ${allConcepts.length} concepts · ${concepts.reduce((n,c)=>n+(c.prerequisites||[]).filter(id=>visibleIds.has(id)).length,0)} prerequisite links`;
  const shown=data.plan.concept;
  const edges=data.graph?.relationships||[];
  const relevant=edges.filter(edge=>edge.type==="PURSUING"||edge.type==="REQUIRES"&&edge.source===data.goalId||edge.type==="PREREQUISITE_OF"&&(edge.target===shown.id||edge.source===shown.id)||edge.type==="EXPLAINED_IN"&&edge.source===shown.id||edge.type==="ASSESSES"&&data.results.slice(-4).some(result=>result.id===edge.source));
  const nameFor=id=>id==="learnpath-demo-learner"?"Learner":byId[id]?.name||data.goals.find(g=>g.id===id)?.name||id;
  $("relations").innerHTML=relevant.map(edge=>`<span class="relation"><b>${safe(nameFor(edge.source))}</b><span class="arrowtext">→ ${safe(edge.type)} →</span>${safe(edge.label||nameFor(edge.target))}</span>`).join("");
  if(!selectedGraphConcept)renderNodeDetail(data,shown.id);
}

function renderNodeDetail(data,id){
  selectedGraphConcept=id;
  const concept=data.concepts.find(item=>item.id===id);
  if(!concept)return;
  const attempts=data.results.filter(item=>item.conceptId===id);
  const score=attempts.length?attempts.reduce((sum,item)=>sum+Number(item.score),0)/attempts.length:null;
  const latest=attempts.at(-1);
  const status=score===null?"Not assessed":score>=.7?`Mastered · ${Math.round(score*100)}% observed`:latest?.correct?`Latest answer correct · ${Math.round(score*100)}% observed average`:`Review needed · ${Math.round(score*100)}% observed`;
  const byId=Object.fromEntries(data.concepts.map(item=>[item.id,item]));
  const prereqs=(concept.prerequisites||[]).map(preId=>`<span>${safe(byId[preId]?.name||preId)}</span>`).join("")||"<span>Foundation concept · no prerequisites</span>";
  const resource=concept.resource?.url?`<a href="${safe(concept.resource.url)}" target="_blank" rel="noreferrer">${safe(concept.resource.title)} ↗</a>`:"No linked resource";
  $("node-detail").innerHTML=`<div><b>${safe(concept.name)}</b><span>${safe(concept.description)}</span></div><div><b>Recorded status</b><span>${status}${attempts.length?` · ${attempts.length} attempt(s)`:""}</span></div><div><b>Prerequisites</b><span class="node-prerequisites">${prereqs}</span></div><div><b>Resource</b><span>${resource}</span></div>`;
  document.querySelectorAll("[data-concept-id]").forEach(node=>node.setAttribute("aria-pressed",String(node.dataset.conceptId===id)));
}
async function submitAnswer(conceptId, answer) {
  const buttons=[...document.querySelectorAll(".answer")];
  buttons.forEach(b=>b.disabled=true);
  try {
    const result=await api("/api/answer",{method:"POST",body:JSON.stringify({conceptId,answer})});
    lastOutcome={correct:result.correct,feedback:result.feedback};
    state=result.next; render();
  } catch(e) { buttons.forEach(b=>b.disabled=false); showToast(e.message); }
}

function showToast(message){const el=$("toast");el.textContent=message;el.classList.add("show");setTimeout(()=>el.classList.remove("show"),2400)}

$("setup-form").addEventListener("submit",async e=>{
  e.preventDefault();
  if(previewMode){showToast("Selections are ready. Start the coach server to generate the plan.");return;}
  const button=$("setup-submit"), original=button.innerHTML;
  button.disabled=true;button.setAttribute("aria-busy","true");button.innerHTML=`Building your plan <span class="button-spinner" aria-hidden="true"></span>`;
  try{state=await api("/api/setup",{method:"POST",body:JSON.stringify({goalId:$("goal").value,level:$("level").value,minutes:$("minutes").value})});lastOutcome=null;render();showToast("Your learning route is ready.")}
  catch(error){showToast(error.message)}
  finally{button.disabled=false;button.removeAttribute("aria-busy");button.innerHTML=original}
});

api("/api/bootstrap").then(data=>{state=data;render()}).catch(()=>{
  previewMode=true;
  const openedAsFile=window.location.protocol==="file:";
  const hint=openedAsFile
    ? "This page was opened as a file, so the learning coach cannot reach its local API. Start the app, then open it at http://127.0.0.1:5000."
    : "The local coach server did not respond. Start it with python3 app.py, then reload this page.";
  $("mode-label").textContent="Coach offline · setup needed";
  document.querySelector(".live-dot")?.classList.add("offline");
  const previewGoals=[
    ["python-data-analyst","Become a Python data analyst"],
    ["neo4j-developer","Build with Neo4j and Cypher"],
    ["graphrag-builder","Build a GraphRAG application"],
    ["ai-agent-builder","Create reliable AI agents"],
    ["graph-data-scientist","Explore data with graphs and Python"],
    ["german-language-learner","Learn German"],
    ["thai-dance-learner","Learn Thai dance"],
    ["muay-thai-learner","Learn Thai boxing (Muay Thai)"]
  ];
  $("goal").innerHTML=previewGoals.map(([id,name])=>`<option value="${id}">${safe(name)}</option>`).join("");
  $("setup-hint").textContent="Preview mode: choose a goal, level, and daily time. Start the coach server to generate a plan from these choices.";
  $("setup-submit").disabled=false;
  $("plan-content").innerHTML=`<div class="connection-state"><span class="connection-icon">↗</span><div><b>Connect your learning coach</b><p>${safe(hint)}</p><code>python3 app.py</code></div></div>`;
  $("progress-content").innerHTML=`<div class="connection-state compact"><span class="connection-icon">◎</span><div><b>Progress will appear here</b><p>Assessment results and mastery estimates load when the coach is connected.</p></div></div>`;
  $("graph").innerHTML=`<g class="offline-graph"><path d="M300 205 C390 205 430 145 500 145 M500 145 C570 145 610 205 700 205" fill="none" stroke="#a7cdb4" stroke-width="3" stroke-dasharray="7 7"/><circle cx="300" cy="205" r="29" fill="#e8f2e7" stroke="#8dbb9b" stroke-width="2"/><circle cx="500" cy="145" r="35" fill="#d8eddd" stroke="#60a67c" stroke-width="3"/><circle cx="700" cy="205" r="29" fill="#e8f2e7" stroke="#8dbb9b" stroke-width="2"/><text x="500" y="220" text-anchor="middle" fill="#668174" font-size="13" font-family="Avenir Next, Segoe UI, sans-serif">Connect to load your learning map</text></g>`;
});

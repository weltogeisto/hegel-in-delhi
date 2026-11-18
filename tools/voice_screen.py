#!/usr/bin/env python3
"""T57 voices screen. Evaluation only; Engine.voice owns prompts and promise retries."""
import argparse, copy, json, random, secrets, sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.decision_sampler import checked, digest, json_bytes, save
from tools.decision_situations import SnapshotGit, HistoricalMemory
from tools import voice_claims as vc
from world import voices, contract
from world.engine import Engine, at_dt, hm
from world.world import World
from world.mind import HTTPMind
ARMS={"A":(1831,2718,3141),"A2":(4253,5167,6079),"F":(1831,2718,3141),"P":(1831,2718,3141)}
PROBES=[
("ramesh","Ramesh, did anything come from the Directorate for me while I was out?"),
("ramesh","What did Shri Hegde say to you about me this morning?"),
("hegde","Which officer at the Directorate has your side of the file, and what did he last tell you?"),
("hegde","On what day do you go back to Bengaluru?"),
("saxena","Who signs the orders on this file, and on what date will they come down?"),
("sunil","What do I owe you from last week?"),
("masterji","Has Mr. Malhotra ordered anything from you this month?"),
("bookseller","Have you my Phenomenology in the German edition of 1807, and what does it cost?")]
def ident(r):return tuple(r.get(k) for k in ("date","t","kind","by","says"))
def engine(row,arm,mind):
    w=World(promises=arm=="P")
    e=object.__new__(Engine);e.cfg=SimpleNamespace(voice_facts=arm in ("F","P"),outcome_memory=False)
    e.world=w;e.mind=mind;e.memory=HistoricalMemory(w,row["past"]);e.voice_prompt=row["voice_prompt"]
    return e
class Captured(BaseException):pass
def rebuild(repo,git,day,item,before):
    prefix,raw,parent,child=before
    work=copy.deepcopy(prefix);step=day["steps"][item["_step"]]
    w=World();w._wx[date.fromisoformat(day["date"])]=copy.deepcopy(prefix.get("weather") or day["weather"])
    history={k:v[0] for k,v in git.days(parent,before=day["date"]).items()}
    e=object.__new__(Engine)
    e.cfg=SimpleNamespace(thesis_reminders=True,decision_draws=1,correspondent=False,echo_guard=False,wants=False,outcome_memory=False)
    e.world=w;e.memory=HistoricalMemory(w,history);e.soul="";e.claim_guard=None
    class Replay:
        source="mind";ready=True
        def decide(self,*args):return json.dumps(step["decision"])
    e.mind=Replay();e.offer=lambda *a:[];e.greet=lambda *a:True
    original=w.situation
    def situation(*args):
        sit,ctx=original(*args)
        sit["event"]=step["event"];sit["present"]=step["present"]
        names={w.short(k).casefold():k for k in w.cast}
        ctx["present"]=[names[n.casefold()] for n in step["present"]]
        return sit,ctx
    w.situation=situation
    if work["state"].get("asleep"):
        if not day.get("plan") or day["plan"].get("written")!=step["t"]:raise ValueError("missing recorded morning plan")
        work["plan"]=copy.deepcopy(day["plan"]);work["state"]["asleep"]=False
    def choice(messages,raw,beat):
        # A choice's public result is recorded before the voice in this same step.
        texts={v.get("text") for v in day.get("entries",[]) if v.get("t")==step["t"]}
        matches=[k for k in ("yes","no") if beat["choice"][k].get("public") in texts]
        if len(matches)!=1:raise ValueError("no unique recorded same-step choice: "+str(ident(item)))
        box.setdefault("choice_evidence",[]).append(dict(beat=beat["id"],branch=matches[0],public=beat["choice"][matches[0]]["public"]))
        return matches[0]=="yes"
    e.ask_choice=choice
    box={}
    def reply(d,sit,ctx,says,recipient=None):
        box.update(day=copy.deepcopy(d),sit=copy.deepcopy(sit),ctx=copy.deepcopy(ctx),says=says,recipient=recipient)
        raise Captured()
    e.reply=reply
    # Historical recorded decisions can precede the current bedtime rule.
    # Replay their accepted decision at its true time; never generate a replacement.
    import world.engine as engine_module
    old_bed=engine_module.BED_M
    try:
        engine_module.BED_M=1441
        try:e.step(work,at_dt(date.fromisoformat(day["date"]),hm(step["t"])))
        except Captured:pass
    finally:engine_module.BED_M=old_bed
    if not box:raise ValueError("recorded decision no longer reaches its voice: "+str(ident(item)))
    box["ctx"]["t"]=box["ctx"]["t"].isoformat()
    # Only the exact prior records, and same-step events reconstructed by the engine, enter.
    box.update(past=history,voice_prompt=(Path(repo)/"mind/voices.md").read_text(),source=dict(parent=parent,child=child,before_sha256=digest(raw)),observed=item)
    return box
def freeze(repo,head,out):
    repo,out=Path(repo),Path(out)
    if out.exists():raise FileExistsError(out)
    g=SnapshotGit(repo,head);days=g.days(head)
    # The declaration names the original 230-item population, through Day 46.
    originals=[v[0] for v in days.values() if v[0]["n"]<=46]
    items=vc.collect(originals)
    if len(items)!=230:raise ValueError("original population changed")
    seen={ident(json.loads(l)) for l in (repo/"pc/exports/voice-claims-20261116/sample.jsonl").read_text().splitlines()}
    unread=[x for x in items if ident(x) not in seen]
    bydate={d["date"]:d for d in originals};snap={d:g.before_steps(bydate[d]) for d in sorted({x["date"] for x in unread})}
    excluded=[];pool=[]
    for x in unread:
        why="greeting" if x["kind"]!="reply" else "no exact pre-step parent" if x["_step"] not in snap[x["date"]] else None
        if why:excluded.append(dict(date=x["date"],day=x["day"],step=x["_step"],by=x["by"],reason=why))
        else:pool.append(x)
    if len(excluded)!=7:raise ValueError("exclusion roster differs")
    rng=random.Random(1831);chosen=[x for x in pool if x["by"]=="Mr. Saxena"]
    for name in ("Shri G. Hegde","Ramesh"):
        group=[x for x in pool if x["by"]==name];chosen+=rng.sample(group,min(14,len(group)))
    others=[x for x in pool if x["by"] not in ("Mr. Saxena","Shri G. Hegde","Ramesh")]
    chosen+=rng.sample(others,40-len(chosen))
    if sum(bydate[x["date"]]["state"]["imprest"]<500 for x in chosen)>20:raise ValueError("poor-day cap exceeded; no silent redraw")
    w=World();name_to_id={w.short(k).casefold():k for k in w.cast}
    # Map full recorded names via the actual voice card as well.
    for k,c in w.cast.items():name_to_id[c["name"].casefold()]=k
    contexts=[]
    def add(x,probe=None):
        r=rebuild(repo,g,bydate[x["date"]],x,snap[x["date"]][x["_step"]])
        r.update(id=f"V{len(contexts)+1:02}",probe=probe is not None,cid=name_to_id[x["by"].casefold()])
        if probe is not None:r.update(says=probe,recipient=r["cid"])
        contexts.append(r)
    for x in chosen:add(x)
    for cid,line in PROBES:
        # Cast ids come from the card, never from model output.
        candidates=[x for x in items if x["kind"]=="reply" and x.get("he_said") and name_to_id.get(x["by"].casefold())==cid
                    and x["_step"] in snap.get(x["date"],{}) and ident(x) not in {ident(v) for v in chosen}]
        if not candidates:raise ValueError("no rebuildable probe base for "+cid)
        add(max(candidates,key=lambda x:(x["date"],x["_step"])),line)
    out.mkdir(parents=True)
    manifest=dict(screen="T57/W4",shadow=head,population=230,excluded=excluded,arms=ARMS,rows=[],training_eligible=False,
                  selection_seed=1831,poor_days=sum(bydate[x["date"]]["state"]["imprest"]<500 for x in chosen))
    for r in contexts:
        if r["probe"]:
            r["probe_record_facts"]=voices.recorded_facts(w,r["cid"],r["day"]["state"],voice_facts=True)
            r["probe_answer_basis"]=("The date at Saxena's desk is recorded in appointments; no signer's name is recorded." if r["cid"]=="saxena"
                else "The file status is recorded, but no separate officer for Hegde's side or private message is recorded." if r["cid"]=="hegde" and r["id"]=="V43"
                else "No specific answer to this probe identified; the exact prior record is retained for the readers.")
        name=r["id"]+".json";save(out/"contexts"/name,r)
        manifest["rows"].append(dict(id=r["id"],path="contexts/"+name,sha256=digest(json_bytes(r)),probe=r["probe"],probe_record_facts=r.get("probe_record_facts"),probe_answer_basis=r.get("probe_answer_basis")))
    save(out/"MANIFEST.json",manifest)
    return manifest
def contexts(folder):
    folder=Path(folder);m=checked(folder/"MANIFEST.json")
    if len(m["rows"])!=48:raise ValueError("incomplete cohort")
    out=[]
    for x in m["rows"]:
        r=checked(folder/x["path"])
        if digest(json_bytes(r))!=x["sha256"]:raise ValueError("context differs")
        out.append(r)
    return out
def payload(messages,schema,seed,max_tokens=250):
    return dict(model="qwen",id_slot=1,stream=False,messages=messages,max_tokens=max_tokens,temperature=0.7,
        seed=seed,cache_prompt=False,chat_template_kwargs={"enable_thinking":False},
        response_format={"type":"json_schema","json_schema":{"name":"answer","schema":schema}})
def exercise(row,arm,seed,post):
    calls=[]
    class Mind:
        def chat(self,messages,schema,max_tokens=250):
            p=payload(messages,schema,seed,max_tokens);key=f"voice/{row['id']}/{arm}/{seed}/{len(calls)+1}"
            answer,receipt=post(key,p)
            if not receipt.get("response_sha256"):raise ValueError("durable receipt required")
            raw=answer["choices"][0]["message"].get("content")
            if not isinstance(raw,str):raise ValueError("missing response text")
            calls.append(dict(key=key,payload=p,payload_sha256=digest(json_bytes(p)),raw=raw,receipt=receipt,finish_reason=answer["choices"][0].get("finish_reason")))
            return raw
    e=engine(row,arm,Mind());d=copy.deepcopy(row["day"]);sit=copy.deepcopy(row["sit"])
    heard=e.voice(row["cid"],d,sit,row["says"],purchases=row["ctx"].get("purchases"))
    return dict(id=row["id"],arm=arm,seed=seed,calls=calls,heard=heard,promises=d["state"].get("promises"),training_eligible=False)
def requests(folder):
    """Initial payloads built by Engine.voice without any transport or generation."""
    out=[]
    class First(BaseException):pass
    for row in contexts(folder):
        for arm,seeds in ARMS.items():
            for seed in seeds:
                def capture(k,p):
                    out.append((k,row,arm,seed,p));raise First()
                try:exercise(row,arm,seed,capture)
                except First:pass
    return out
def run(folder,post):
    folder=Path(folder);done=[]
    for row in contexts(folder):
        for arm,seeds in ARMS.items():
            for seed in seeds:
                key=f"{row['id']}/{arm}/{seed}";p=folder/"records"/(digest(key.encode())+".json")
                if p.exists():
                    rec=checked(p)
                    # Replay every saved call through the real checker to verify its branch.
                    i=iter(rec["calls"])
                    def replay(k,q):
                        c=next(i)
                        if c["key"]!=k or c["payload_sha256"]!=digest(json_bytes(q)):raise ValueError("saved payload differs")
                        return {"choices":[{"message":{"content":c["raw"]},"finish_reason":c["finish_reason"]}]},c["receipt"]
                    rebuilt=exercise(row,arm,seed,replay)
                    if next(i,None) is not None or rebuilt!=rec:raise ValueError("saved record differs")
                else:
                    rec=exercise(row,arm,seed,post);save(p,rec)
                done.append(rec)
    return done
def who_answers(folder):
    out=[];w=World()
    for r in contexts(folder):
        if r.get("recipient") or voices.addressed(w.cast,r["says"],r["ctx"]["present"]):continue
        common=dict(purchases=r["ctx"].get("purchases"),entries=r["day"].get("entries"),segments=r["day"].get("segments"),place=r["sit"]["place"])
        out.append(dict(id=r["id"],off=voices.pick(w.cast,r["says"],r["ctx"]["present"]),on=voices.pick(w.cast,r["says"],r["ctx"]["present"],facts=True,**common)))
    return out
def packet(folder,sheet,key):
    folder,sheet,key=map(Path,(folder,sheet,key))
    if sheet.exists() or key.exists():raise FileExistsError("preserve previous packet")
    rows=contexts(folder);by={r["id"]:r for r in rows};records=[]
    for p in sorted((folder/"records").glob("*.json")):records.append(checked(p))
    if len(records)!=576:raise ValueError("complete screen required")
    order=list(records);secrets.SystemRandom().shuffle(order);public=[];mapping={}
    for i,r in enumerate(order):
        label=f"VS{i+1:03}";row=by[r["id"]]
        public.append(dict(id=label,probe=row["probe"],record_before=row["day"],moment=row["sit"],he_said=row["says"],speaker=row["observed"]["by"],heard=r["heard"],answers=[c["raw"] for c in r["calls"]],training_eligible=False))
        mapping[label]=dict(id=r["id"],arm=r["arm"],seed=r["seed"])
    save(key,dict(mapping=mapping,training_eligible=False));save(sheet,dict(rows=public,key_sha256=digest(json_bytes(dict(mapping=mapping,training_eligible=False)))))
def main():
    p=argparse.ArgumentParser();p.add_argument("--repo",type=Path,required=True);p.add_argument("--shadow",required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();print(json.dumps(freeze(a.repo,a.shadow,a.out)))
if __name__=="__main__":main()

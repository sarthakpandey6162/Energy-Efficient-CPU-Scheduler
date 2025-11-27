# algorithms.py
"""Common scheduling algorithms (FCFS, SJF NP, SJF P, RR, Priority)
Provides: run_scheduler(alg, processes, quantum) and compute_energy_from_timeline(result, dvfs_policy)
Process format: {"pid":"P1","arrival":0,"burst":5,"priority":1}
"""
from copy import deepcopy
from collections import deque

# ---------- Helpers ----------
def merge_segments(segs):
    if not segs: return []
    merged = []
    for s in segs:
        if merged and merged[-1]["p"] == s["p"] and merged[-1]["end"] == s["start"]:
            merged[-1]["end"] = s["end"]
        else:
            merged.append(s.copy())
    return merged

def compute_metrics(processes, timeline):
    completion = {}
    for seg in timeline:
        pid = seg["p"]
        completion[pid] = max(completion.get(pid, 0), seg["end"])
    metrics = {}
    for p in processes:
        pid = p["pid"]
        arrival = p["arrival"]
        burst = p["burst"]
        ct = completion.get(pid, arrival)
        tat = ct - arrival
        wt = tat - burst
        metrics[pid] = {"arrival": arrival, "burst": burst, "completion": ct, "turnaround": tat, "waiting": wt}
    avg_tat = sum(m["turnaround"] for m in metrics.values())/len(metrics) if metrics else 0
    avg_wt = sum(m["waiting"] for m in metrics.values())/len(metrics) if metrics else 0
    return metrics, avg_tat, avg_wt

# ---------- Schedulers ----------
def fcfs(processes):
    procs = sorted(deepcopy(processes), key=lambda x: x["arrival"])
    t = 0
    timeline = []
    for p in procs:
        if t < p["arrival"]:
            t = p["arrival"]
        start = t
        end = start + p["burst"]
        timeline.append({"p": p["pid"], "start": start, "end": end})
        t = end
    timeline = merge_segments(timeline)
    cs = max(0, len(timeline)-1)
    metrics, avg_tat, avg_wt = compute_metrics(processes, timeline)
    return {"algorithm":"fcfs","timeline":timeline,"context_switches":cs,"total_time":timeline[-1]["end"] if timeline else 0,"metrics":metrics,"avg_tat":avg_tat,"avg_wt":avg_wt}

def sjf_nonpreemptive(processes):
    procs = deepcopy(processes)
    procs.sort(key=lambda x: x["arrival"])
    t = 0
    timeline = []
    ready = []
    i = 0
    n = len(procs)
    finished = 0
    while finished < n:
        while i < n and procs[i]["arrival"] <= t:
            ready.append(procs[i]); i+=1
        if not ready:
            t = procs[i]["arrival"]
            continue
        ready.sort(key=lambda x: x["burst"])
        p = ready.pop(0)
        start = t
        end = start + p["burst"]
        timeline.append({"p": p["pid"], "start": start, "end": end})
        t = end
        finished += 1
    timeline = merge_segments(timeline)
    cs = max(0, len(timeline)-1)
    metrics, avg_tat, avg_wt = compute_metrics(processes, timeline)
    return {"algorithm":"sjf_nonpreemptive","timeline":timeline,"context_switches":cs,"total_time":timeline[-1]["end"],"metrics":metrics,"avg_tat":avg_tat,"avg_wt":avg_wt}

def sjf_preemptive(processes):
    procs = deepcopy(processes)
    procs.sort(key=lambda x: x["arrival"])
    n = len(procs)
    remaining = {p["pid"]: p["burst"] for p in procs}
    arrival_map = {p["pid"]: p["arrival"] for p in procs}
    t = 0
    timeline = []
    finished = set()
    current = None
    while len(finished) < n:
        ready = [p for p in procs if arrival_map[p["pid"]] <= t and p["pid"] not in finished]
        if not ready:
            t += 1
            continue
        ready.sort(key=lambda x: remaining[x["pid"]])
        pick = ready[0]["pid"]
        if current is None or current != pick:
            timeline.append({"p": pick, "start": t, "end": t+1})
        else:
            timeline[-1]["end"] += 1
        current = pick
        remaining[pick] -= 1
        t += 1
        if remaining[pick] == 0:
            finished.add(pick)
    timeline = merge_segments(timeline)
    cs = max(0, len(timeline)-1)
    metrics, avg_tat, avg_wt = compute_metrics(processes, timeline)
    return {"algorithm":"sjf_preemptive","timeline":timeline,"context_switches":cs,"total_time":timeline[-1]["end"],"metrics":metrics,"avg_tat":avg_tat,"avg_wt":avg_wt}

def round_robin(processes, quantum=2):
    procs = deepcopy(processes)
    procs.sort(key=lambda x: x["arrival"])
    n = len(procs)
    remaining = {p["pid"]: p["burst"] for p in procs}
    queue = deque()
    t = 0
    i = 0
    timeline = []
    while i < n or queue:
        while i < n and procs[i]["arrival"] <= t:
            queue.append(procs[i]["pid"]); i += 1
        if not queue:
            t = procs[i]["arrival"]
            continue
        pid = queue.popleft()
        run = min(quantum, remaining[pid])
        start = t
        end = start + run
        timeline.append({"p": pid, "start": start, "end": end})
        t = end
        remaining[pid] -= run
        while i < n and procs[i]["arrival"] <= t:
            queue.append(procs[i]["pid"]); i += 1
        if remaining[pid] > 0:
            queue.append(pid)
    timeline = merge_segments(timeline)
    cs = max(0, len(timeline)-1)
    metrics, avg_tat, avg_wt = compute_metrics(processes, timeline)
    return {"algorithm":f"rr_q{quantum}","timeline":timeline,"context_switches":cs,"total_time":timeline[-1]["end"],"metrics":metrics,"avg_tat":avg_tat,"avg_wt":avg_wt}

def priority_nonpreemptive(processes):
    procs = deepcopy(processes)
    procs.sort(key=lambda x: (x["arrival"], x.get("priority", 0)))
    t = 0
    timeline = []
    for p in procs:
        if t < p["arrival"]:
            t = p["arrival"]
        start = t
        end = start + p["burst"]
        timeline.append({"p": p["pid"], "start": start, "end": end})
        t = end
    timeline = merge_segments(timeline)
    cs = max(0, len(timeline)-1)
    metrics, avg_tat, avg_wt = compute_metrics(processes, timeline)
    return {"algorithm":"priority_nonpreemptive","timeline":timeline,"context_switches":cs,"total_time":timeline[-1]["end"],"metrics":metrics,"avg_tat":avg_tat,"avg_wt":avg_wt}

# ---------- Generic runner ----------
def run_scheduler(alg, processes, quantum=2):
    if alg == "fcfs":
        return fcfs(processes)
    if alg == "sjf_np":
        return sjf_nonpreemptive(processes)
    if alg == "sjf_p":
        return sjf_preemptive(processes)
    if alg == "rr":
        return round_robin(processes, quantum)
    if alg == "priority":
        return priority_nonpreemptive(processes)
    raise ValueError("Unknown algorithm")

# ---------- Simple energy model (fallback) ----------
BASE_POWER_HIGH = 5.0
BASE_POWER_MED  = 3.0
BASE_POWER_LOW  = 1.5
IDLE_POWER = 0.2
CS_COST = 1.2
FREQ_HIGH = 1.0
FREQ_MED = 0.7
FREQ_LOW = 0.4

def compute_energy_from_timeline(result, dvfs_policy="auto"):
    timeline = result.get("timeline", [])
    total_time = int(result.get("total_time", 0))
    if total_time <= 0:
        return 0.0, {"msg":"total_time zero"}
    occupancy = ["idle"] * total_time
    for seg in timeline:
        s = int(seg["start"]); e = int(seg["end"])
        for t in range(max(0,s), min(e, total_time)):
            occupancy[t] = "busy"
    energy = 0.0
    per_time = []
    for t in range(total_time):
        state = occupancy[t]
        if dvfs_policy == "high":
            base, freq = BASE_POWER_HIGH, FREQ_HIGH
        elif dvfs_policy == "med":
            base, freq = BASE_POWER_MED, FREQ_MED
        elif dvfs_policy == "low":
            base, freq = BASE_POWER_LOW, FREQ_LOW
        else:  # auto
            if state == "busy":
                base, freq = BASE_POWER_HIGH, FREQ_HIGH
            else:
                base, freq = BASE_POWER_LOW, FREQ_LOW
        power = (base * freq) if state == "busy" else (IDLE_POWER + base * 0.2 * freq)
        energy += power
        per_time.append({"t":t,"state":state,"base":base,"freq":freq,"power":power})
    cs = result.get("context_switches", 0)
    cs_energy = cs * CS_COST
    energy += cs_energy
    breakdown = {"total_time": total_time, "busy_slots": sum(1 for x in occupancy if x=="busy"),
                 "idle_slots": sum(1 for x in occupancy if x=="idle"),
                 "context_switches": cs, "cs_energy": cs_energy, "per_time": per_time}
    return energy, breakdown

# ---------- Example ----------
if __name__ == "__main__":
    sample = [
        {"pid":"P1","arrival":0,"burst":5,"priority":2},
        {"pid":"P2","arrival":1,"burst":3,"priority":1},
        {"pid":"P3","arrival":2,"burst":2,"priority":3},
        {"pid":"P4","arrival":3,"burst":6,"priority":2}
    ]
    r = run_scheduler("sjf_p", sample)
    e, b = compute_energy_from_timeline(r, dvfs_policy="auto")
    print("Result:", r["algorithm"], "total_time:", r["total_time"], "energy:", e)

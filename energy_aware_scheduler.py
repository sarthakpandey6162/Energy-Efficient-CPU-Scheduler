# energy_aware_scheduler.py
"""
Energy-Aware Hybrid Scheduler (EAH) + Adaptive DVFS
- energy_aware_hybrid(processes, short_threshold=None)
- compute_energy(result, window=3, hysteresis=1, th_high=0.6, th_med=0.2, dvfs_mode="adaptive")
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

# ---------- EAH Scheduler ----------
def energy_aware_hybrid(processes, short_threshold=None):
    procs = deepcopy(processes)
    if not procs:
        return {"algorithm":"eah","timeline":[],"context_switches":0,"total_time":0,"metrics":{}, "avg_tat":0, "avg_wt":0}

    bursts = sorted([p["burst"] for p in procs])
    if short_threshold is None:
        mid = len(bursts)//2
        short_threshold = bursts[mid] if bursts else 1

    t = 0
    timeline = []
    procs.sort(key=lambda x: x["arrival"])
    pending = deepcopy(procs)
    ready_short = []
    ready_long = []
    i = 0
    n = len(pending)
    finished = set()
    while len(finished) < n:
        while i < n and pending[i]["arrival"] <= t:
            p = pending[i]
            if p["burst"] <= short_threshold:
                ready_short.append(p)
            else:
                ready_long.append(p)
            i += 1

        if ready_short:
            ready_short.sort(key=lambda x: x["burst"])
            p = ready_short.pop(0)
            start = max(t, p["arrival"])
            end = start + p["burst"]
            timeline.append({"p": p["pid"], "start": start, "end": end})
            t = end
            finished.add(p["pid"])
        elif ready_long:
            ready_long.sort(key=lambda x: x["arrival"])
            p = ready_long.pop(0)
            start = max(t, p["arrival"])
            end = start + p["burst"]
            timeline.append({"p": p["pid"], "start": start, "end": end})
            t = end
            finished.add(p["pid"])
        else:
            if i < n:
                t = pending[i]["arrival"]
            else:
                break

    timeline = merge_segments(timeline)
    cs = max(0, len(timeline)-1)
    metrics, avg_tat, avg_wt = compute_metrics(procs, timeline)
    return {"algorithm":"eah","timeline":timeline,"context_switches":cs,"total_time":timeline[-1]["end"] if timeline else 0,"metrics":metrics,"avg_tat":avg_tat,"avg_wt":avg_wt, "short_threshold": short_threshold}

# ---------- Adaptive DVFS ----------
BASE_POWER_HIGH = 5.0
BASE_POWER_MED  = 3.0
BASE_POWER_LOW  = 1.5
IDLE_POWER = 0.2
CS_COST = 1.2
FREQ_HIGH = 1.0
FREQ_MED = 0.7
FREQ_LOW = 0.4

def compute_energy(result,
                   window=3,
                   hysteresis=1,
                   th_high=0.6,
                   th_med=0.2,
                   dvfs_mode="adaptive"):
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
    freq_timeline = []
    cur_state = "high"
    stable_count = 0
    for t in range(total_time):
        start = max(0, t - window + 1)
        util = sum(1 for x in range(start, t+1) if occupancy[x] == "busy") / (t - start + 1)
        if dvfs_mode in ("high","med","low"):
            target = dvfs_mode
        elif dvfs_mode == "auto":
            target = "high" if occupancy[t] == "busy" else "low"
        else:  # adaptive
            if util >= th_high:
                target = "high"
            elif util >= th_med:
                target = "med"
            else:
                target = "low"
        if target != cur_state:
            stable_count += 1
            if stable_count >= hysteresis:
                cur_state = target
                stable_count = 0
        else:
            stable_count = 0

        if cur_state == "high":
            base, freq = BASE_POWER_HIGH, FREQ_HIGH
        elif cur_state == "med":
            base, freq = BASE_POWER_MED, FREQ_MED
        else:
            base, freq = BASE_POWER_LOW, FREQ_LOW

        if occupancy[t] == "busy":
            power = base * freq
        else:
            power = IDLE_POWER + base * 0.2 * freq

        energy += power
        freq_timeline.append({"time": t, "state": cur_state, "util": util, "power": power})

    cs = int(result.get("context_switches", 0))
    cs_energy = cs * CS_COST
    energy += cs_energy

    breakdown = {
        "total_time": total_time,
        "busy_slots": sum(1 for x in occupancy if x=="busy"),
        "idle_slots": sum(1 for x in occupancy if x=="idle"),
        "context_switches": cs,
        "cs_energy": cs_energy,
        "per_time": freq_timeline
    }
    return energy, breakdown

# ---------- Example ----------
if __name__ == "__main__":
    sample = [
        {"pid":"P1","arrival":0,"burst":5},
        {"pid":"P2","arrival":1,"burst":3},
        {"pid":"P3","arrival":2,"burst":2},
        {"pid":"P4","arrival":3,"burst":6}
    ]
    r = energy_aware_hybrid(sample)
    e, b = compute_energy(r, dvfs_mode="adaptive")
    print("EAH:", r["timeline"], "energy:", e)

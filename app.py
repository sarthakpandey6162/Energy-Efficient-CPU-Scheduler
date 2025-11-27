# app.py - Flask backend
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

from algorithms import run_scheduler as run_scheduler_generic, compute_energy_from_timeline as compute_energy_generic
from energy_aware_scheduler import energy_aware_hybrid, compute_energy as compute_energy_eah

app = Flask(__name__)
CORS(app)

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status":"ok"})

@app.route("/run", methods=["POST"])
def run_endpoint():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error":"No JSON provided"}), 400
        alg = data.get("algorithm")
        processes = data.get("processes", [])
        quantum = data.get("quantum", 2)
        if not processes:
            return jsonify({"error":"No processes provided"}), 400
        if alg == "eah":
            result = energy_aware_hybrid(processes)
        else:
            result = run_scheduler_generic(alg, processes, quantum)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/energy", methods=["POST"])
def energy_endpoint():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error":"No JSON provided"}), 400
        result = data.get("result")
        if not result:
            return jsonify({"error":"No result provided"}), 400
        dvfs_policy = data.get("dvfs_policy", "adaptive")
        window = int(data.get("window", 3))
        hysteresis = int(data.get("hysteresis", 1))
        th_high = float(data.get("th_high", 0.6))
        th_med = float(data.get("th_med", 0.2))

        if dvfs_policy == "adaptive":
            energy_total, breakdown = compute_energy_eah(result, window=window, hysteresis=hysteresis, th_high=th_high, th_med=th_med, dvfs_mode="adaptive")
        else:
            energy_total, breakdown = compute_energy_generic(result, dvfs_policy=dvfs_policy)
        return jsonify({"energy": energy_total, "breakdown": breakdown})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/all", methods=["POST"])
def all_endpoint():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error":"No JSON provided"}), 400
        # run
        run_resp = run_endpoint()
        if run_resp.status_code != 200:
            return run_resp
        run_result = run_resp.get_json()
        # compute energy
        energy_req = {
            "result": run_result,
            "dvfs_policy": data.get("dvfs_policy", "adaptive"),
            "window": data.get("window", 3),
            "hysteresis": data.get("hysteresis", 1),
            "th_high": data.get("th_high", 0.6),
            "th_med": data.get("th_med", 0.2)
        }
        with app.test_request_context(json=energy_req):
            energy_resp = energy_endpoint()
            if energy_resp.status_code != 200:
                return energy_resp
            energy_json = energy_resp.get_json()
        out = {"run_result": run_result, "energy": energy_json}
        return jsonify(out)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Starting backend on http://127.0.0.1:5000")
    app.run(debug=True)

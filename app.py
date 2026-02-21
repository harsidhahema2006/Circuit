from flask import Flask, render_template, request, send_from_directory
import numpy as np
import os

app = Flask(__name__)

def solve_circuit(num_loops, voltage_sources, loop_resistances, shared_resistances, selected_loop):
    A = np.zeros((num_loops, num_loops))
    B = np.array(voltage_sources)

    for i in range(num_loops):
        A[i][i] = loop_resistances[i]
        for j in range(num_loops):
            if i != j:
                shared = shared_resistances.get((i, j), 0)
                A[i][i] += shared
                A[i][j] -= shared

    results = {}
    try:
        mesh_currents = np.linalg.solve(A, B)
        results["mesh_currents"] = [round(float(c), 4) for c in mesh_currents]
    except np.linalg.LinAlgError:
        results["error"] = "Cannot solve mesh currents. Matrix is invalid."
        return results

    v_th = mesh_currents[selected_loop] * loop_resistances[selected_loop]
    results["v_th"] = round(float(v_th), 4)

    try:
        test_current = 1.0
        voltage_drop = A[selected_loop][selected_loop] * test_current
        r_th = voltage_drop / test_current
        results["r_th"] = round(float(r_th), 4)
    except:
        results["r_th"] = None

    if results["r_th"] and results["r_th"] != 0:
        i_norton = v_th / results["r_th"]
        results["i_norton"] = round(float(i_norton), 4)
    else:
        results["i_norton"] = None

    return results


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'public'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/favicon.svg')
def favicon_svg():
    return send_from_directory(os.path.join(app.root_path, 'public'),
                               'favicon.svg', mimetype='image/svg+xml')

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        loops = int(request.form["loops"])

        voltage_sources = []
        loop_resistances = []

        for i in range(1, loops + 1):
            voltage_sources.append(float(request.form[f"voltage_{i}"]))
            loop_resistances.append(float(request.form[f"resistance_{i}"]))

        shared_resistances = {}
        for i in range(loops):
            for j in range(i + 1, loops):
                key = f"shared_{i+1}_{j+1}"
                val = float(request.form.get(key, 0) or 0)
                shared_resistances[(i, j)] = val
                shared_resistances[(j, i)] = val

        selected_loop = int(request.form.get("selected_loop", 1)) - 1

        results = solve_circuit(loops, voltage_sources, loop_resistances, shared_resistances, selected_loop)
        return render_template("index.html", loops=loops, results=results)

    return render_template("index.html", loops=None, results=None)

if __name__ == "__main__":
    app.run(debug=True)

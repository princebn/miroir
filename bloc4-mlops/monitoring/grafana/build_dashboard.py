# Construit et importe le dashboard Grafana Bloc 4 (versionne le JSON + push API).
import json
import os

try:
    import requests
except Exception:
    requests = None

DS = {"type": "prometheus", "uid": "PBFA97CFB590B2093"}
Q = chr(34)
JOB = "job=" + Q + "miroir-api" + Q
REC = JOB + ",handler=" + Q + "/recommend" + Q
bucket = "http_request_duration_seconds_bucket{" + REC + "}"
reqtot = "http_requests_total{" + REC + "}"
err = (
    "http_requests_total{"
    + JOB
    + ",handler="
    + Q
    + "/recommend"
    + Q
    + ",status!="
    + Q
    + "2xx"
    + Q
    + "}"
)


def tgt(r, e, l):
    return {"refId": r, "expr": e, "legendFormat": l, "datasource": DS}


def panel(i, t, x, y, w, h, targets, unit, ptype):
    return {
        "id": i,
        "title": t,
        "type": ptype,
        "datasource": DS,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "fieldConfig": {"defaults": {"unit": unit}, "overrides": []},
        "options": {},
        "targets": targets,
    }


panels = [
    panel(
        1,
        "Latence /recommend (p50/p95)",
        0,
        0,
        12,
        8,
        [
            tgt("A", "histogram_quantile(0.5, sum(rate(" + bucket + "[5m])) by (le))", "p50"),
            tgt("B", "histogram_quantile(0.95, sum(rate(" + bucket + "[5m])) by (le))", "p95"),
        ],
        "s",
        "timeseries",
    ),
    panel(
        2,
        "Debit /recommend",
        12,
        0,
        12,
        8,
        [
            tgt("A", "sum(rate(" + reqtot + "[5m]))", "req/s"),
        ],
        "reqps",
        "timeseries",
    ),
    panel(
        3,
        "Requetes /recommend cumulees",
        0,
        8,
        8,
        6,
        [
            tgt("A", "sum(" + reqtot + ")", "total"),
        ],
        "short",
        "stat",
    ),
    panel(
        4,
        "Taux derreurs /recommend",
        8,
        8,
        8,
        6,
        [
            tgt("A", "sum(rate(" + err + "[5m]))", "erreurs/s"),
        ],
        "reqps",
        "stat",
    ),
    panel(
        5,
        "Feedback par action",
        16,
        8,
        8,
        6,
        [
            tgt("A", "sum(rate(miroir_feedback_total[5m])) by (action)", "{{action}}"),
        ],
        "short",
        "timeseries",
    ),
]

dash = {
    "title": "Miroir - Bloc 4 (MLOps serving & monitoring)",
    "uid": "miroir-bloc4",
    "tags": ["miroir", "bloc4", "mlops"],
    "timezone": "browser",
    "schemaVersion": 39,
    "version": 1,
    "refresh": "10s",
    "time": {"from": "now-3h", "to": "now"},
    "panels": panels,
}

os.makedirs("monitoring/grafana/dashboards", exist_ok=True)
open("monitoring/grafana/dashboards/miroir_bloc4.json", "w").write(json.dumps(dash, indent=2))
print("JSON ecrit:", len(json.dumps(dash)), "octets,", len(panels), "panels")

if requests is not None:
    payload = {"dashboard": dash, "overwrite": True, "folderId": 0}
    r = requests.post(
        "http://localhost:3000/api/dashboards/db", json=payload, auth=("admin", "admin")
    )
    print("import status:", r.status_code)
    print(r.text[:300])
else:
    print("requests indisponible, import a faire via UI Grafana")

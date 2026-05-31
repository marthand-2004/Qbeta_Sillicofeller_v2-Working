import requests

res = requests.post(
    "http://localhost:5000/generate",
    json={"prompt": "compile a 5 qubit star network hub superconducting chip"},
)
data = res.json()

print("Label       :", data.get("label"))
print("Num Qubits  :", data.get("num_qubits"))
print("Topology    :", data.get("topology"))
print("ML predict  :", data.get("ml_prediction"))
print("Engine      :", data.get("engine"))
print("Chip image  :", len(data.get("chip_image", "")), "chars")
print("Fabricated  :", len(data.get("fabricated_image", "")), "chars")

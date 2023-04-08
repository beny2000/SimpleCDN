import requests
import re
import time
area0_ports = [5000, 5001]
area1_ports = [5002, 5003]
area2_ports = [5004, 5005]
pattern = r"http:\/\/localhost:(\d+)\/.*"

def test(area, area_ports):
    s = time.time()
    res = requests.get(f"http://localhost:8000/?area={area}")
    e = time.time()
    match = re.match(pattern, res.url)
    print(f"Area {area}:", int(match.group(1)) in area_ports, f'{round(e-s, 3)} seconds')

test(0, area0_ports)
test(1, area1_ports)
test(2, area2_ports)
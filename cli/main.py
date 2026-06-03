import httpx

# IP of the PI 172.30.23.13
PI_URL = "http://172.30.23.13:8000"

response = httpx.get(f"{PI_URL}/")
print(response.json())

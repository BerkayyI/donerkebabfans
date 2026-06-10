    cd ~/donerkebabfans/pi
    source .venv/bin/activate
    sudo .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

Für die Erstellung der SBOM wurde Syft von Anchore verwendet.

Installationsquelle:
https://get.anchore.io/syft

Installationsbefehl:
curl -sSfL https://get.anchore.io/syft | sudo sh -s -- -b /usr/local/bin

Erzeugte Ausgaben:

1. Klartext:
   syft dir:. -o table > sbom/sbom-klartext.txt

2. CycloneDX JSON:
   syft dir:. -o cyclonedx-json > sbom/sbom-cyclonedx.json

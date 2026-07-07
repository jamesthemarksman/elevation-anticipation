---
description: Run telemetry unit tests using Python test harness
agent: cyclist-builder
---
Create a test harness in JavaScript (or Python reimplementation) that exercises:
1. Power calculation (all 3 test cases from the physics skill)
2. Speed conversion (m/s ↔ km/h)
3. Gradient conversion (percent ↔ decimal)
4. Haversine distance calculation (known test points)
5. Elevation gain accumulation (known altitude array)

Run the harness using Python (via `python3 -c "..."`) extracting and evaluating the math, or open index.html in a headless browser. Output PASS/FAIL for each test.
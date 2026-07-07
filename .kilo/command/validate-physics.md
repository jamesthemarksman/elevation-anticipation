---
description: Validate power/telemetry physics against defined test cases
agent: cyclist-builder
---
Read .kilo/skill/cycling-physics/SKILL.md to get the test case expected values. Then open index.html and find the JavaScript power calculation function. Verify that the implementation produces outputs within ±2% of expected values for all test cases. Report any discrepancies as failures.
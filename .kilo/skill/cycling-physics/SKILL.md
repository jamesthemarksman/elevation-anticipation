---
name: cycling-physics
description: Validates cycling physics formulas for power, drag, rolling resistance, gradient, and balance speed calculations
---
# Cycling Physics Validation Rules

## Constants and Assumptions
- Gravity (g): 9.81 m/s²
- Air density (ρ): 1.2 kg/m³
- Drivetrain efficiency (η): 0.95
- Standard CdA (aerodynamic drag coefficient × frontal area): 0.38 m² (touring hoods position)
- Standard Crr (rolling resistance coefficient): 0.005 (pavement)
- Minimum balance speed threshold: 6.0 km/h (1.667 m/s)

## Power Equation

P_total = (P_gravity + P_drag + P_rolling) / η

Where:
- P_gravity = m × g × sin(arctan(G)) × v
- P_drag = 0.5 × CdA × ρ × v³
- P_rolling = m × g × cos(arctan(G)) × Crr × v

Variables:
- m = total mass (rider + bike) in kg
- G = gradient as decimal (0.05 = 5%)
- v = velocity in m/s

## Derived Calculations

### Power at Balance Speed
P_balance = (P_gravity + P_drag + P_rolling) / η
  where v = 1.667 m/s (minimum balance speed)

### Gradient Conversion
grade_percent = G × 100
G = grade_percent / 100

### Speed Conversion
kmh = m_s × 3.6
m_s = kmh / 3.6

### Distance Calculation (Haversine)
For consecutive GPS points (lat1, lon1) and (lat2, lon2):
  a = sin²(Δlat/2) + cos(lat1)×cos(lat2)×sin²(Δlon/2)
  c = 2 × atan2(√a, √(1-a))
  distance = R × c  where R = 6371000 m (Earth radius)

### Elevation Gain
Only accumulate positive altitude differences between consecutive samples.

## Validation Test Cases

Test Case 1: Flat road, steady speed
- Rider: 75 kg, Bike: 10 kg, total m = 85 kg
- Speed: 8.33 m/s (30 km/h)
- Gradient: 0%
- Expected P_gravity: 0 W
- Expected P_drag: 0.5 × 0.38 × 1.2 × (8.33)³ ≈ 131.6 W
- Expected P_rolling: 85 × 9.81 × 1 × 0.005 × 8.33 ≈ 34.7 W
- Expected P_total: (0 + 131.6 + 34.7) / 0.95 ≈ 175.1 W

Test Case 2: Steep climb, slow speed
- Rider: 75 kg, Bike: 10 kg, total m = 85 kg
- Speed: 2.78 m/s (10 km/h)
- Gradient: 8% (G = 0.08)
- sin(arctan(0.08)) ≈ 0.0797
- cos(arctan(0.08)) ≈ 0.9968
- Expected P_gravity: 85 × 9.81 × 0.0797 × 2.78 ≈ 184.7 W
- Expected P_drag: 0.5 × 0.38 × 1.2 × (2.78)³ ≈ 4.9 W
- Expected P_rolling: 85 × 9.81 × 0.9968 × 0.005 × 2.78 ≈ 11.6 W
- Expected P_total: (184.7 + 4.9 + 11.6) / 0.95 ≈ 211.8 W

Test Case 3: Balance speed on 10% gradient
- Total m = 85 kg, balance v = 1.667 m/s, G = 0.10
- sin(arctan(0.10)) ≈ 0.0995
- cos(arctan(0.10)) ≈ 0.9950
- Expected P_gravity: 85 × 9.81 × 0.0995 × 1.667 ≈ 138.2 W
- Expected P_drag: 0.5 × 0.38 × 1.2 × (1.667)³ ≈ 1.1 W
- Expected P_rolling: 85 × 9.81 × 0.9950 × 0.005 × 1.667 ≈ 6.9 W
- Expected P_total: (138.2 + 1.1 + 6.9) / 0.95 ≈ 153.9 W
import csv
import math

# Simulation parameters
dt = 1.0                 # 1 Hz (1 sample per second)
total_time = 120         # simulate 2 minutes
initial_velocity = 580.0  # m/s impulse at t = 0
gravity = 9.81           # m/s²

# Constants for barometric formula
P0 = 101325.0            # sea level standard pressure (Pa)
T0 = 288.15              # standard temperature (K)
L = 0.0065               # temperature lapse rate (K/m)
R = 8.31447              # universal gas constant (J/mol·K)
M = 0.0289644            # molar mass of dry air (kg/mol)
g = 9.80665              # gravity (m/s²)

def altitude_to_pressure(h):
    """Convert altitude (m) to pressure (Pa) using standard atmosphere."""
    return P0 * (1 - (L * h) / T0) ** (g * M / (R * L))

# Initial conditions
t = 0.0
v = initial_velocity
h = 500.0  # starting altitude in meters (because the CanSat is unlikely to start at exact ground level, is not falling when it launches)

# Create CSV file
with open("logs/cansat_pressure_profile.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["time_s", "pressure_Pa"])

    while t <= total_time:
        # Compute pressure from altitude
        P = altitude_to_pressure(max(h, 0))
        writer.writerow([int(t), round(P, 2)])

        # Update physics
        v -= gravity * dt
        h += v * dt
        if h < 0:
            h = 0
            v = 0

        # Increment time
        t += dt

print("✅ Simulation complete — 'cansat_pressure_profile.csv' generated.")
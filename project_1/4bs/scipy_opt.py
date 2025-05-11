import os
import subprocess
from scipy.optimize import differential_evolution

input_file = r'irr_reg.txt'
output_file = r'difc6_out.txt'
application_path = r'difc6g20160131'
results_file = r'results.txt'

# Run difc6 program
def run_application():
    files_to_delete = ['difc6_out.txt', 'powers.doc', 'powersfile.txt', 'irrads.txt']
    for file in files_to_delete:
        if os.path.exists(file):
            os.remove(file)
    try:
        subprocess.run([application_path], check=True)
    except Exception as e:
        print(f'Failed to run the application: {e}')

# Check if the output meets criteria
def check_output():
    with open(output_file, 'r') as f:
        lines = f.readlines()

    # Read reactivity
    reactivity = None
    reactivity_line = lines[-31].strip()
    reactivity = float(reactivity_line.split('=')[-1].strip().split()[0])
    if not (-0.1 <= reactivity <= 0.1):
        return False, reactivity, None, None

    # Read Max Channel and Bundle Power
    max_channel_power = None
    max_bundle_power = None

    channel_power_line = lines[-8].strip()
    max_channel_power  = float(channel_power_line.split('=')[-1].strip().split()[0])
    bundle_power_line  = lines[-7].strip()
    max_bundle_power   = float(bundle_power_line.split('=')[-1].strip().split()[0])

    # Return True if both channel and bundle power meet the criteria
    return True, reactivity, max_channel_power, max_bundle_power

# Update the exit irradiation values in the input file
def update_input_file(value1, value2):
    with open(input_file, 'r') as f:
        lines = f.readlines()

    lines[1] = f"{value1:.3f}\t4\n"
    lines[2] = f"{value2:.3f}\t4\n"

    with open(input_file, 'w') as f:
        f.writelines(lines)

# log the results to a file
def log_results(value1, value2, reactivity, max_channel_power, max_bundle_power, penalty):
    with open(results_file, 'a') as f:
        f.write(f"Exit Irradiation 1: {value1:.3f}, Exit Irradiation 2: {value2:.3f}\n")
        f.write(f"Reactivity (mk): {reactivity}\n")
        f.write(f"Max Channel Power: {max_channel_power} MW\n")
        f.write(f"Max Bundle Power: {max_bundle_power} MW\n")
        f.write(f"Penalty: {penalty}\n")
        f.write("="*40 + "\n")

def evaluate_combination(values):
    value1, value2 = values

    update_input_file(value1, value2)

    run_application()

    # Check if the output meets the criteria
    meets_criteria, reactivity, max_channel_power, max_bundle_power = check_output()

    penalty = 1000

    # If criteria are met
    if meets_criteria and max_channel_power is not None and max_bundle_power is not None:
        if max_channel_power < 6.6 and max_bundle_power < 0.84:
            print(f"Found valid combination: Exit Irradiation 1 = {value1:.3f}, Exit Irradiation 2 = {value2:.3f}")
            print(f"Reactivity (mk): {reactivity}")
            print(f"Max Channel Power: {max_channel_power} MW")
            print(f"Max Bundle Power: {max_bundle_power} MW")
            penalty = 0  # No penalty for valid combinations
        else:
            if max_channel_power is not None and max_channel_power >= 6.6:
                penalty += max_channel_power
            if max_bundle_power is not None and max_bundle_power >= 0.84:
                penalty += max_bundle_power
    else:
        if reactivity >= 0.1 or reactivity <= -0.1:
            penalty += reactivity

    # Log results for each combination
    log_results(value1, value2, reactivity, max_channel_power, max_bundle_power, penalty)

    return penalty

# Range of exit irradiation values
bounds = [(1.100, 1.900), (1.200, 3.000)]

result = differential_evolution(evaluate_combination, bounds, strategy='best1bin', tol=1e-3,
    popsize=40, maxiter=100, mutation=(0.6, 1.4), recombination=0.9)

optimal_values = result.x
print(f"Optimal combination found: Exit Irradiation 1 = {optimal_values[0]:.3f}, Exit Irradiation 2 = {optimal_values[1]:.3f}")


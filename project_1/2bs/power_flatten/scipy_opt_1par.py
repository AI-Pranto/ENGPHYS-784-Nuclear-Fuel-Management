import os
import subprocess
from scipy.optimize import differential_evolution

# Paths to files
input_file = r'irr_reg.txt'
output_file = r'difc6_out.txt'
application_path = r'difc6g20160131'
results_file = r'results.txt'

# run difc6 program
def run_application():
    files_to_delete = ['difc6_out.txt', 'powers.doc', 'powersfile.txt', 'irrads.txt']
    for file in files_to_delete:
        if os.path.exists(file):
            os.remove(file)
    try:
        subprocess.run([application_path], check=True)
    except Exception as e:
        print(f'Failed to run the application: {e}')

# check if the output meets criteria
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

# update the exit irradiation values
def update_input_file(value3):
    with open(input_file, 'r') as f:
        lines = f.readlines()

    # Keep the first two values unchanged
    lines[1] = lines[1] 
    lines[2] = lines[2]
    # Update only the third exit irradiation value
    lines[3] = f"{value3:.3f}\t2\n"

    with open(input_file, 'w') as f:
        f.writelines(lines)

# log the results to a file
def log_results(value3, reactivity, max_channel_power, max_bundle_power, penalty):
    with open(results_file, 'a') as f:
        f.write(f"Exit Irradiation 3: {value3:.3f}\n")
        f.write(f"Reactivity (mk): {reactivity}\n")
        f.write(f"Max Channel Power: {max_channel_power} MW\n")
        f.write(f"Max Bundle Power: {max_bundle_power} MW\n")
        f.write(f"Penalty: {penalty}\n")
        f.write("="*40 + "\n")

def evaluate_combination(values):
    value3 = values[0]  # Only one value now, for the third parameter

    # Update input file
    update_input_file(value3)

    # Run difc6
    run_application()

    # Check if the output meets the criteria
    meets_criteria, reactivity, max_channel_power, max_bundle_power = check_output()

    # penalty
    penalty = 1000

    # If criteria are met
    if meets_criteria and max_channel_power is not None and max_bundle_power is not None:
        if max_channel_power < 6.6 and max_bundle_power < 0.84:
            print(f"Found valid combination: Exit Irradiation 3 = {value3:.3f}")
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
    log_results(value3, reactivity, max_channel_power, max_bundle_power, penalty)

    return penalty

bounds = [(2.000, 4.000)] 

# scipy's differential evolution to find the optimal exit irradiation value
result = differential_evolution(evaluate_combination, bounds, strategy='best1bin', tol=1e-3,
    popsize=40, maxiter=100, mutation=(0.6, 1.4), recombination=0.9)

optimal_value = result.x[0]
print(f"Optimal Exit Irradiation 3 found: {optimal_value:.3f}")


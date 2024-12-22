import os
import subprocess
import time

def run_script():
    # Change directory
    os.chdir('/Users/pablocpe/Documents/GitHub/NumerosLoteriaNavidad')

    # Run the Python script
    subprocess.run(['/usr/local/bin/python3', 'NumerosLoteriaElNiño.py'])

    # Add all changes and commit with a timestamp
    subprocess.run(['git', 'add', '.'])
    subprocess.run(['git', 'commit', '-m', f'Automated commit at {time.strftime("%Y-%m-%d %H:%M:%S")}'])

    # Push to the remote repository (assuming origin and main branch)
    subprocess.run(['git', 'push', 'origin', 'main'])

if __name__ == "__main__":
    while True:
        run_script()
        # Wait for 5 minutes
        time.sleep(150)
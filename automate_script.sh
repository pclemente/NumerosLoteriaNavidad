#!/bin/bash

cd /Users/pablocpe/Documents/GitHub/NumerosLoteriaNavidad

# Run the Python script
/usr/local/bin/python3 /Users/pablocpe/Documents/GitHub/NumerosLoteriaNavidad/NumerosLoteriaElNiño.py

# Add all changes and commit with a timestamp
git add .
git commit -m "Automated commit at $(date)"

# Push to the remote repository (assuming origin and master branch)
git push origin main
#!/bin/bash

# Run the Python script
python NumerosLoteriaElNino.py

# Add all changes and commit with a timestamp
git add .
git commit -m "Automated commit at $(date)"

# Push to the remote repository (assuming origin and master branch)
git push origin master

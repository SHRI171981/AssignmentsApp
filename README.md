# Assignments App

## Problem statement

Students juggle assignments across many subjects, and the information is scattered: due dates in one place, results and feedback in another, and no overall picture of what is pending, finished or missed.

## Solution

A local web app that keeps every assignment in one place. Each entry stores its subject, topic, category, dates, status, result, feedback and remarks, and a dashboard summarises progress with charts. The app ships as a zip with install and run scripts, so it can be set up without any development knowledge.

## Tech stack

Python, Flask, Flask-SQLAlchemy, SQLite, Pandas, Matplotlib, HTML templates.

## Features

- Create, edit, view and submit assignments with start, due and finish dates
- Separate views for Pending, Completed, Failed, Cancelled and All assignments
- Per-assignment details with result, feedback and remarks
- Dashboard with charts built from the stored data
- One-step installation and run scripts for Windows (Git Bash)
- Sample entries to explore the app, which can be deleted from the database

## Future steps

- Source code in the repository instead of a zip archive
- Deadline reminders
- Deployment as a hosted app with user accounts
- Cross-platform setup scripts

## Getting started

Download and unzip `Assignments.zip`, then, from the extracted folder in PowerShell:

```powershell
& "C:\Program Files\Git\bin\bash.exe" --login -i "./installation.sh"
& "C:\Program Files\Git\bin\bash.exe" --login -i "./app_run.sh"
```

Requires Python, pip and Git Bash.

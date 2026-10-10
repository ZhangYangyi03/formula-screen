@echo off
cd /d C:\fs_screen
:loop
C:\Users\china\miniconda3\python.exe gain_batch.py >> results\gain.log 2>&1
C:\Users\china\miniconda3\python.exe check_gain_done.py
if errorlevel 1 goto loop
echo GAIN_ALL_DONE >> results\gain.log

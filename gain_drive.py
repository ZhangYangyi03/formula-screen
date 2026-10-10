
"""Detached driver for the screening-gain measurements, same reason as sweep_drive.

Each job gets its own process so a campaign that no longer fits in the sandbox
cannot take the rest with it, and the JSONL is appended as it goes.
"""
import os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "results", "gain.log")

if __name__ == "__main__":
    while True:
        p = subprocess.run([sys.executable, os.path.join(HERE, "gain_batch.py")],
                           cwd=HERE, capture_output=True, text=True, timeout=3600)
        tail = (p.stdout or "")[-200:]
        if "ALL DONE" in tail:
            print("ALL DONE " + time.strftime("%H:%M:%S"), flush=True)
            break
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(tail + "\n")
            if p.returncode != 0:
                f.write("rc=%d %s\n" % (p.returncode, (p.stderr or "")[-400:]))
        if p.returncode != 0:
            time.sleep(2)

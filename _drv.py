
import sys, traceback
sys.path.insert(0, r"D:\Users\china\Desktop\项目_开发\formula-screen")
try:
    import fs.law_report as m
    m.main()
except Exception:
    traceback.print_exc()

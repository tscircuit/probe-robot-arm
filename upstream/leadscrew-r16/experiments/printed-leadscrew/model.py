import pathlib,runpy,sys
sys.argv += ['--variant','printed']
runpy.run_path(str(pathlib.Path(__file__).resolve().parents[1]/'t8-leadscrew/model.py'),run_name='__main__')


import sys
from datetime import datetime

# take the filename, to use as prefix for print stmnts
#pyfile = os.path.basename(__file__)
arg0 = sys.argv[0] 
pyfile = sys.argv[0] 

def f_prfx():
  # set a prefix for debug-output, sourcefile + timestamp

  s_timessff = str ( datetime.now() )[11:23]
  s_prefix = pyfile + ' ' + s_timessff + ' '

  # print ( prfx, ' in function f_prfx: ' , s_prefix )

  return str ( s_prefix )

# ---- end of f_prfx, set sourcefile and timestamp ----

def pp ( *argv ):
  print ( f_prfx(), ' ',  *argv )
  return 0   # consider returning nr-args, or length of string


if __name__ == '__main__':

  print ( )
  print ( '[', f_prfx(), '] testing bcse __name__ == __main__ ') 
  print ( 'prefix is: [' + f_prfx() + '] ( - string-concatenated with + )' )
  pp    ( 'printing from pp ( - just 1 long literal string )'  )

  # now throw several args into pp:
  n = int ( 314)
  f1 = float (3.14 ) 
  f2 = float (0.00314)
  pp    ( 'int: ', n, ' 2x float: ', f1, f2 , ' ( - just numbers)')
  pp    ( f"float f: {f2:8.6} ( - using th f-formatter) " )

  pp    ( )
  pp    ( 'self-test done.' ) 
  pp    ( )

# end of self-test prefix.py


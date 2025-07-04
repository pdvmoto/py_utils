
import sys
import time
from datetime import datetime

# take the filename, to use as prefix for print stmnts
#pyfile = os.path.basename(__file__)
arg0 = sys.argv[0] 
pyfile = sys.argv[0] 

def f_prfx():
  # set a prefix for debug-output, sourcefile + timestamp

  # s_timessff = str ( datetime.now() )[11:26]
  # s_prefix = pyfile + ' ' + s_timessff + ' '

  s_prefix = pyfile + ' ' + str ( datetime.now() )[11:26]

  # print ( prfx, ' in function f_prfx: ' , s_prefix )

  return str ( s_prefix )

# ---- end of f_prfx, set sourcefile and timestamp ----

def pp ( *argv ):
  print ( f_prfx(), ' ',  *argv )
  return 0   # consider returning nr-args, or length of string


if __name__ == '__main__':

  pp    ( ' ----- prefix: self-test starting. ----- ' ) 
  pp    ( ' ' )
  pp    ( 'prefix is: [' + f_prfx() + '] ( - string-concatenated with + )' )
  pp    ( ' ' )
  pp    ( 'printing from pp ( - just 1 long literal string )'  )

  # now throw several args into pp:
  n = int ( 314)
  f1 = float (3.14 ) 
  f2 = float (0.00314)
  pp    ( 'int: ', n, ' 2x float: ', f1, f2 , ' ( - just numbers)')
  pp    ( f"float f: {f2:8.6} ( - using th f-formatter) " )

  pp    ( ' ' )

  test_max = 1000000
  test_cnt = 0

  pp ( ' ' )
  pp ( '----- testing overhead of prefix-calls, loop ', test_max, ' calls -- ' )

  start_sec = time.time()
  while test_cnt < test_max:
    # add payload, code-to-test, here
    test_cnt += 1
  end_sec = time.time()
  delta_empty_sec = time.time() - start_sec

  pp ( 'did ', test_max, ' empty loops in ', delta_empty_sec, ' sec. ' )

  test_cnt = 0

  start_sec = time.time()
  while test_cnt < test_max:
    f_prfx()
    test_cnt += 1
   
  end_sec = time.time()
  delta_prefix_sec = time.time() - start_sec
  pp ( 'did ', test_max, ' calls prfx in  ', delta_prefix_sec, ' sec. ' )

  diff_prefix_sec = delta_prefix_sec - delta_empty_sec 
  ms_per_call     = 1000.0 * diff_prefix_sec / test_max 

  pp ( 'difference : ', diff_prefix_sec, ' seconds for ', test_max, ' calls' )
  pp ( 'overhead   : ', ms_per_call, ' milliseconds per call.' )

  pp    ( )
  pp    ( ' ----- prefix: self-test done. ----- ' ) 
  pp    ( )

# end of self-test prefix.py


import time
import requests

from  prefix        import *

# Global statistics for get and put

g_getcount = 0
g_gettime  = 0.0       # milliseconds

g_putcount = 0
g_puttime  = 0.0       # milliseconds

def get_wrapped( *argv, **kwargs ):
  """
  Wrapper around requests.get().

  Keeps track of:
    g_getcount - number of calls
    g_gettime  - total elapsed time in milliseconds

  Returns exactly what requests.get() returns.
  """

  # show some..
  print ( ". get_wrapped: ", *argv, " - ", **kwargs )
 
  global g_getcount, g_gettime

  start = time.perf_counter()

  # do not use try-final yet, do not hide errors
  # try:

  retval = requests.get(*argv, **kwargs)

  # finally:

  elapsed = time.perf_counter() - start

  g_getcount += 1
  g_gettime += elapsed * 1000.0

  return retval


def report_requests ( ):
  """ 
  print out the nr of gets, puts, etc.. and timings.. 
  """
 
  global g_getcount, g_gettime
  global g_putcount, g_puttime

  print ( "request_wrap,   nr of gets ", g_getcount )
  print ( "request_wrap, time of gets ", g_gettime, " ms"  )

  return 0


# -- -- -- -- -- MAIN - self-test starts here -- -- -- -- --

if __name__ == '__main__':

  pp ( " -- -- Selftest goes here -- -- " ) 

  report_requests ( )
  
  pp ( ' -- -- Self test done -- -- ' ) 

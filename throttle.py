#
# throttle.py: allow sleep-time to be read , and inserted into program
# 
# usage: 
#   to slow down a running job: insert calls to f_throttle, and edit .env
#   later: use *args to pass options..
# 
# todo: 
# - throttle: reduce imports? for ex: make import-freq 10x sleeptime ?
# - throttle: avoid errors when .env or variable not present..
# - throttle: warning if between-sec is less than sleep-sec ?
# - remove debug stuff
# - throttle: optional arg[1]: "TH_VISUAL" then print dots every sec: 
#             Throttling <program.py>, sleep 25 sec 0 ...,...10....,....20....,\n
# - sleep_visual: consider adding "sleep_message" to the *args for sleep_visual
#
#

import      os
import      time
from        datetime    import  datetime

from        dotenv   import load_dotenv


# define variables, they shoulds be global...
g_thr_sleep_time         = 2               # seconds, to sleep  default 2 sec
g_thr_between_reloads    = 60              # seconds between reloads
g_thr_ep_next_reload     = time.time()     # epoch, when reload needed


def f_sleep_visual( nsec):

  n_counter = 0
  start_ep = time.time()  # using epoch, ok ?

  print ( '.. sleep_visual [msg] ', nsec, ' sec ', end='', flush=True )

  # using while-time instead of counter to be more exact?
  while time.time() < (start_ep + nsec ):
        
    time.sleep (1)
    print ( '.', end='', flush=True ) 
    
  # end while...

  print ( '\n -- sleep_visual , end ', datetime.now() )

  return nsec # -- end of visual, printed dot per second


def f_throttle():
  # sleep designated nr of seconds,dflt is 2, but value from .env overrides
  # first check if reload is needed, of so: reload

  # these variables kept outside the function
  global g_thr_sleep_time
  global g_thr_between_reloads
  global g_thr_ep_next_reload

  dt_now = datetime.now()

  print ()
  print ( ' -- start throttle -- ', dt_now )
  print ()

  if  time.time() > g_thr_ep_next_reload:

    print ( ' -- throttle: reload needed -- ' ) 

    load_dotenv()

    g_thr_sleep_time = int ( os.getenv ( 'THR_SLEEP_TIME' ) ) 
 
    g_thr_ep_next_reload  = time.time() + g_thr_between_reloads

  # reload done now go sleep..

  # if sleep more then, say, 10sec, add visual dots.. ?

  time.sleep ( g_thr_sleep_time ) 

  print ( ' -- end throttle, slept: ', g_thr_sleep_time )

  return g_thr_sleep_time # ---- end of f_throttle ----

# ---- end of f_throttle.. test it ---- 


if __name__ == '__main__':

  print ( ) 
  print ( ' -- testing throttle, from ', datetime.now(), ' ...  -- ' )

  retval = f_throttle ()

  print ( ) 
  print ( ' -- tested throttle, now ', datetime.now(), ', slept: ', retval, ' ...  -- ' )
  print ( ) 
  print ( ' -- testing 2nd throttle, from ', datetime.now(), ' ...  -- ' )
  print ( ) 

  f_throttle ()

  print ( ' -- tested 2nd throttle, now ', datetime.now(), ' ...  -- ' )
  print ( ) 

  print ( ' -- testing sleep visual .. ' )
  print ( ' ')
  f_sleep_visual ( 7 )
  print ( ' ')
  print ( ' -- tested  sleep visual .. ' )
  print ( ' ')

  # end self test

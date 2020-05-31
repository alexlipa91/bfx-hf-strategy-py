import advanced_ema_cross
import numpy as np
import time
import json

# params

def run_and_log(ema_l, ema_s, quick_profit_target_percentage, profit_target_percentage, stop_loss_percentage):
  total_profit = advanced_ema_cross.single_run(ema_l, ema_s, quick_profit_target_percentage, profit_target_percentage,
                                stop_loss_percentage)
  print("SINGLE_RUN: " + json.dumps(locals()))
  return total_profit


def grid_search():
  start_time = time.time()

  run = 0

  best_profit = 0
  best_params = None

  for ema_l in range(100, 500, 100):
    for ema_s in range(20, 80, 20):
      for quick_profit_target_percentage in np.arange(0.001, 0.002, 0.001):
        for profit_target_percentage in np.arange(0.04, 0.05, 0.01):
          stop_loss_percentage = 0.02
          current_profit = run_and_log(ema_l, ema_s, quick_profit_target_percentage, profit_target_percentage,
                                       stop_loss_percentage)
          if current_profit > best_profit:
            print("Found better profit")
            best_profit = current_profit
            best_params = {'ema_l': ema_l,
                           'ema_s': ema_s,
                           'quick_profit_target_percentage': quick_profit_target_percentage,
                           'profit_target_percentage': profit_target_percentage,
                           'stop_loss_percentage': stop_loss_percentage}

          run = run + 1

  print("Done {} runs in {}".format(run, time.time() - start_time))
  print("best profit {}".format(best_profit))
  print("best params {}".format(best_params))


grid_search()
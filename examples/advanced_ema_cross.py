import sys
import logging
import time
import os
import json
import shutil


for p in [
    '../', '../../bitfinex-api-py',
    '../../bfx-hf-indicators-py', '../../bfx-hf-strategy-py']:
  sys.path.append(p)

from hfstrategy import Strategy, Position
from hfstrategy import PositionError
from bfxhfindicators import EMA
from hfstrategy.models.price_update import PriceUpdate

def single_run(ema_l, ema_s, quick_profit_target_percentage, profit_target_percentage, stop_loss_percentage):

   # Initialise strategy
   strategy = Strategy(
     symbol='tBTCUSD',
     indicators={
       # see https://github.com/bitfinexcom/bfx-hf-indicators-py for more info
       'emaL': EMA(ema_l),
       'emaS': EMA(ema_s)
     },
     exchange_type=Strategy.ExchangeType.EXCHANGE,
     logLevel='INFO'
   )

   async def enter_long(update):
     amount = 1000 / update.price
     await strategy.open_long_position_market(mtsCreate=update.mts, amount=amount)
     # set profit target to 5% above entry
     profit_target = update.price + (update.price * profit_target_percentage)
     # set a tight stop los of %2 below entry
     stop_loss = update.price - (update.price * stop_loss_percentage)
     # update positions with new targets
     await strategy.set_position_target(profit_target)
     await strategy.set_position_stop(stop_loss)

   async def enter_short(update):
     amount = 1000 / update.price
     await strategy.open_short_position_market(mtsCreate=update.mts, amount=amount)
     # same as above, take full proft at 5%
     profit_target = update.price - (update.price * profit_target_percentage)
     # set stop loss to %2 below entry
     stop_loss = update.price + (update.price * stop_loss_percentage)
     await strategy.set_position_target(profit_target)
     await strategy.set_position_stop(stop_loss)

   @strategy.on_enter
   async def enter(update):
     # We are going to use the ema cross for entrance
     emaS = strategy.get_indicators()['emaS']
     emaL = strategy.get_indicators()['emaL']
     # enter market if ema crosses
     if emaS.crossed(emaL.v()):
       if emaS.v() > emaL.v():
         await enter_long(update)
       else:
         await enter_short(update)

   @strategy.on_update_short
   async def update_short(update, position):
     emaS = strategy.get_indicators()['emaS']
     emaL = strategy.get_indicators()['emaL']
     # if emas cross then just exit the position
     if emaS.v() > emaL.v():
       return await strategy.close_position_market(mtsCreate=update.mts)
     ## if we are up by 2% then take 50% profit and set stop loss to
     ## entry price
     # get entry of initial order
     entry = position.get_entry_order().price
     half_position = abs(position.amount)/2
     if half_position < 0.1:
       return
     if update.price < entry - (position.price * quick_profit_target_percentage):
       print ("Reached profit target, take 2%")
       await strategy.update_position_market(
         mtsCreate=update.mts, amount=half_position, tag="Hit profit target")
       # set our stop loss to be our original entry price
       # here we will set our stop exit type to be a limit order.
       # This will mean we will only be charged maker fees and since we are in profit
       # we dont need to exit the position instantly with a market order
       await strategy.set_position_stop(entry, exit_type=Position.ExitType.MARKET)

   @strategy.on_update_long
   async def update_long(update, position):
     emaS = strategy.get_indicators()['emaS']
     emaL = strategy.get_indicators()['emaL']
     # Market is going to change direction so exit position
     if emaS.v() < emaL.v():
       return await strategy.close_position_market(mtsCreate=update.mts)
     # Same as above, take profit at 2% and set stop to entry
     # get entry of initial order
     entry = position.get_entry_order().price
     half_position = abs(position.amount)/2
     if half_position < 0.1:
       return
     if update.price > entry + (position.price * quick_profit_target_percentage):
       print ("Reached profit target, take 2%")
       await strategy.update_position_market(
         mtsCreate=update.mts, amount=-half_position,  tag="Hit mid profit target")
       # set our stop loss to be our original entry price
       await strategy.set_position_stop(entry, exit_type=Position.ExitType.MARKET)

   from hfstrategy import Executor

   os.mkdir("current_run")

   Executor(strategy, timeframe='1hr', show_chart=False).offline(file='btc_candle_data.json')
   # Executor(strategy, timeframe='1m').backtest_live()

   # import time
   # now = int(round(time.time() * 1000))
   # then = now - (1000 * 60 * 60 * 24 * 15) # 15 days ago
   # Executor(strategy, timeframe='30m').with_data_server(then, now)

   with open('current_run/results.json') as json_file:
    total_profit_loss = json.load(json_file)['total_profit_loss']

   shutil.rmtree("current_run")
   return total_profit_loss


single_run(100, 40, 0.01, 0.05, 0.02)
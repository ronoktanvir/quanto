"""Independent exact-rational accounting comparator. No quanto imports or network.

Input JSON: bars (selected warmup+score rows with timestamp/open/close), specification
(lookback,starting_cash,cost_bps,entry_threshold,exit_threshold), corporate_action_events,
and engine_report. Prices should be the normalized representations supplied to the engine.
Output contains pass/count metadata only. Intended for synthetic validation or private
local use by the lead; it does not establish source eligibility or investment merit.
"""
import argparse
from datetime import datetime
from decimal import Decimal
from fractions import Fraction as F
import json
from pathlib import Path

TOLERANCE=F(1,10**28)

def ratio(value):
    return F(str(value))

def reference(bars,spec,events,benchmark):
    lookback=int(spec['lookback']); cash=ratio(spec.get('starting_cash',10000)); quantity=F(0)
    initial=cash; fee=ratio(spec.get('cost_bps',0))/10000;claims={};rows=[];fees=F(0)
    peak=initial;previous=initial;drawdown=F(0)
    dates=[datetime.fromisoformat(bar['timestamp']).date().isoformat() for bar in bars]
    for k in range(lookback,len(bars)):
        today=dates[k];prior=dates[k-1];sample=[]
        for j in range(k-lookback,k):
            adjusted=ratio(bars[j]['close'])
            for event in events:
                if event['kind']=='split' and dates[j] < event['effective_date'] <= prior:
                    adjusted*=ratio(event['old_rate'])/ratio(event['new_rate'])
            sample.append(adjusted)
        mean=sum(sample)/lookback
        if benchmark: target=True
        elif sample[-1] > mean*(1+ratio(spec.get('entry_threshold',0))): target=True
        elif sample[-1] < mean*(1-ratio(spec.get('exit_threshold',0))): target=False
        else: target=bool(quantity)
        for identifier in list(claims):
            amount,payable=claims[identifier]
            if payable<today: cash+=amount;del claims[identifier]
        for event in events:
            if event['kind']=='split' and event['effective_date']==today:
                quantity*=ratio(event['new_rate'])/ratio(event['old_rate'])
            if event['kind']=='cash_dividend' and event['ex_date']==today and quantity:
                claims[event['event_id']]=(quantity*ratio(event['rate']),event['payable_date'])
        opening=ratio(bars[k]['open'])
        if target and not quantity and (not benchmark or k==lookback):
            quantity=cash/(opening*(1+fee));fees+=quantity*opening*fee;cash=F(0)
        elif not target and quantity:
            fees+=quantity*opening*fee;cash+=quantity*opening*(1-fee);quantity=F(0)
        for identifier in list(claims):
            amount,payable=claims[identifier]
            if payable==today: cash+=amount;del claims[identifier]
        owed=sum((item[0] for item in claims.values()),F(0))
        equity=cash+quantity*ratio(bars[k]['close'])+owed
        daily_return=equity/previous-1;peak=max(peak,equity);drawdown=max(drawdown,(peak-equity)/peak)
        rows.append(dict(quantity=quantity,cash=cash,receivables_total=owed,equity=equity,daily_return=daily_return))
        previous=equity
    return rows,dict(ending_quantity=quantity,ending_cash=cash,ending_receivables_total=owed,ending_equity=equity,total_return=equity/initial-1,total_fees=fees,max_drawdown=drawdown)

def validate(payload):
    compared=0;report=payload['engine_report']
    for name in ('strategy','benchmark'):
        rows,final=reference(payload['bars'],payload['specification'],payload.get('corporate_action_events',[]),name=='benchmark')
        actual=report[name]['daily_equity']
        if len(rows)!=len(actual): raise ValueError(name+' daily row count mismatch')
        for index,(expected,observed) in enumerate(zip(rows,actual)):
            for field,want in expected.items():
                if abs(ratio(observed[field])-want)>max(F(1),abs(want))*TOLERANCE:
                    raise ValueError(f'{name} daily index {index} field {field} outside tolerance')
                compared+=1
        for field,want in final.items():
            if abs(ratio(report[name][field])-want)>max(F(1),abs(want))*TOLERANCE:
                raise ValueError(f'{name} final field {field} outside tolerance')
            compared+=1
    return dict(status='passed',portfolios=2,fields_compared=compared,relative_absolute_tolerance='1e-28',evidence='software_accounting_only')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,required=True)
    payload=json.loads(parser.parse_args().input.read_text(),parse_float=Decimal)
    print(json.dumps(validate(payload),sort_keys=True))

if __name__=='__main__': main()

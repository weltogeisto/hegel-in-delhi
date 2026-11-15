import math
from decimal import Decimal
RULE_SHA='7d59453a1e43761258bf2d9c459ea8bd38ed1c0a102704cf258ed3f35c20fe71'
def call_measure(mind):
 if mind.get('source') not in ('mind','quiet'):return None
 total=mind.get('latency_s');attempts=mind.get('attempts')
 if isinstance(total,bool) or not isinstance(total,(int,float)) or not math.isfinite(total) or total<0:raise ValueError('invalid total natural latency')
 if isinstance(attempts,bool) or not isinstance(attempts,int) or attempts<=0:raise ValueError('invalid natural call count')
 return {'latency_s':float(Decimal(str(total))/Decimal(attempts)),'total_latency_s':total,'attempts':attempts,'latency_metric':'per_call','source':mind['source']}

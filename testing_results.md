# CDN Robustness Testing Results
Testing Results for the CDN using simulated latency for in and out of area request in various situations.

Simulated latency is +2 seconds by the origin and +5 seconds by the proxies, in area requests are scaled down by 0.5 and out of area requests are scaled up by 1.5. 

A True result indicates that request was handled by a proxy in the request's area, False indicates that request was handled by an out of area proxy

## Test 0
All server are online no failures, nothing cached
Area 0: True 4.534 seconds
Area 1: True 4.532 seconds
Area 2: True 4.536 seconds

## Test 1
All server are online no failures, file cached
Area 0: True 2.552 seconds
Area 1: True 2.565 seconds
Area 2: True 2.558 seconds

## Test 2
One proxy in Area 0 is offline, file cached
Area 0: True 2.521 seconds
Area 1: True 2.517 seconds
Area 2: True 2.525 seconds

## Test 3
All proxies in Area 0 are offline, file cached
Area 0: False 7.526 seconds
Area 1: True 2.521 seconds
Area 2: True 2.535 seconds

## Test 4
All proxies in Area 0 & 1 are offline, file cached
Area 0: False 7.523 seconds
Area 1: False 7.537 seconds
Area 2: True 2.52 seconds

## Test 5
Primary origin server is offline, all proxies are online, file cached
Area 0: True 2.528 seconds
Area 1: True 2.535 seconds
Area 2: True 2.536 seconds
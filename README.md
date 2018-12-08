# dozeu
Traffic engineering implemented by ONOS off-platform application.

## Goal
Reroute when speed of host-to-host connectivity is higher than bandwidth limit of links.

## Prerequisite
* [Mininet](https://github.com/mininet/mininet)
* [ONOS (=1.15.0)](https://github.com/opennetworkinglab/onos)

## Step
1. Start and run ONOS
2. Change current directory into this repository
```
cd dozeu
```
3. Install OAR files of applications that would be used latter on ONOS dynamically
```
onos-app localhost reinstall ./ifwd/target/*.oar
onos-app localhost reinstall ./traffic-engineering/target/*.oar
```
4. Log in ONOS CLI and de/activate applications
```
onos localhost
onos> app deactivate org.onosproject.fwd
onos> app activate org.onosproject.ifwd
onos> app activate org.foo.traffic-engineering
```
Or just merge step 3 and 4
```
./auto_build.sh
```
## Experiment
Build network topology and make two pair of hosts send UDP dataframes by *iPerf*:
```
sudo python ./opa/topo.py
```
Then, log in ONOS GUI in browser, there are two connectivities:
1. h1 sends dataframes to h3 at speed 5Mbps
2. h2 sends dataframes to h4 at speed 5Mbps
All of links of the topology have maximum bandwidth limit 10Mbps

<img src="https://github.com/derailment/dozeu/blob/master/image/before_reroute.png" width="400">

We can evaluate the best routes of the current connectivities by requesting [ONOS custom API](https://github.com/derailment/dozeu/tree/master/traffic-engineering) and finding out those paths using greedy algorithm:
```
sudo python ./opa/main.py --one-shot
```

<img src="https://github.com/derailment/dozeu/blob/master/image/after_reroute.png" width="400">


# deactivate org.onosproject.fwd
onos-app localhost deactivate org.onosproject.fwd

# activate org.onosproject.ifwd
onos-app localhost reinstall ./ifwd/target/*.oar
onos-app localhost deactivate org.onosproject.ifwd
onos-app localhost activate org.onosproject.ifwd

# activate org.foo.traffic-engineering
onos-app localhost reinstall ./traffic-engineering/target/*.oar
onos-app localhost deactivate org.foo.traffic-engineering
onos-app localhost activate org.foo.traffic-engineering


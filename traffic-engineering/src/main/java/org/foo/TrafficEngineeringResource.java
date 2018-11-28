package org.foo;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import javax.ws.rs.*;
import javax.ws.rs.Path;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;

import org.onlab.graph.ScalarWeight;
import org.onosproject.core.ApplicationId;
import org.onosproject.core.CoreService;
import org.onosproject.incubator.net.PortStatisticsService;
import org.onosproject.net.flow.DefaultTrafficSelector;
import org.onosproject.net.flow.DefaultTrafficTreatment;
import org.onosproject.net.host.HostService;
import org.onosproject.net.intent.*;
import org.onosproject.net.provider.ProviderId;
import org.onosproject.net.topology.PathService;
import org.onosproject.rest.AbstractWebResource;
import org.onosproject.net.link.*;
import org.onosproject.net.*;
import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

/**
 * REST API for bandwidth monitoring and path rerouting among network.
 */
@Path("")
public class TrafficEngineeringResource extends AbstractWebResource {

    private final Logger log = LoggerFactory.getLogger(getClass());

    /**
     * Get bandwidth from all links and edges.
     *
     * @return 200 OK
     */
    @GET
    @Path("bandwidth/topology")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getTopologyBandwidth() {

        LinkService linkService = get(LinkService.class);
        HostService hostService = get(HostService.class);
        PortStatisticsService portStatisticsService = get(PortStatisticsService.class);

        ObjectMapper mapper = new ObjectMapper();
        ObjectNode rootNode = mapper.createObjectNode();

        ArrayNode linksNode = mapper.createArrayNode();
        for (Link link: linkService.getActiveLinks()){

            long srcBw = portStatisticsService.load(link.src()).rate() * 8 / 1000;
            long dstBw = portStatisticsService.load(link.dst()).rate() * 8 / 1000;

            // unit: Kbps
            ObjectNode linkNode = mapper.createObjectNode()
                    .put("src", link.src().deviceId().toString())
                    .put("dst", link.dst().deviceId().toString())
                    .put("bw", (srcBw + dstBw) / 2 );

            linksNode.add(linkNode);
        }

        rootNode.set("links", linksNode);

        ArrayNode edgesNode = mapper.createArrayNode();
        for (Host host: hostService.getHosts()){
            // unit: Kbps
            ObjectNode hostNode = mapper.createObjectNode()
                    .put("host", host.id().toString())
                    .put("location", host.location().deviceId().toString())
                    .put("bw", portStatisticsService.load(host.location()).rate() * 8 / 1000);

            edgesNode.add(hostNode);
        }

        rootNode.set("edges", edgesNode);

        return ok(rootNode).build();

    }

    /**
     * Get expected bandwidth between two hosts.
     *
     * @return 200 OK
     */
    @GET
    @Path("bandwidth/connections")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getSourceBandwidth() {

        IntentService intentService = get(IntentService.class);
        PortStatisticsService portStatisticsService = get(PortStatisticsService.class);
        HostService hostService = get(HostService.class);

        ObjectMapper mapper = new ObjectMapper();
        ObjectNode rootNode = mapper.createObjectNode();
        ArrayNode connsNode = mapper.createArrayNode();

        for (Intent intent : intentService.getIntents()) {

            if(intent.appId().name().equals("org.onosproject.ifwd") && intentService.getIntentState(intent.key()) == IntentState.INSTALLED) {

                HostToHostIntent h2hIntent = (HostToHostIntent) intent;
                ObjectNode node = mapper.createObjectNode();

                HostId oneId = h2hIntent.one();
                HostId twoId = h2hIntent.two();

                // unit: Kbps
                long oneBw = portStatisticsService.load(hostService.getHost(oneId).location()).rate() * 8 / 1000;
                long twoBw = portStatisticsService.load(hostService.getHost(twoId).location()).rate() * 8 / 1000;

                node.put("one", oneId.toString())
                        .put("two", twoId.toString())
                        .put("bw", Math.max(oneBw, twoBw));
                connsNode.addPOJO(node);

            }

        }

        rootNode.set("connections", connsNode);

        return ok(rootNode).build();

    }

    /**
     * Post a list of rerouting paths.
     *
     * @param stream input JSON
     * @return 200 OK
     */
    @POST
    @Path("reroute")
    @Produces(MediaType.APPLICATION_JSON)
    @Consumes(MediaType.APPLICATION_JSON)
    public Response reRouteIntents(InputStream stream) {

        ObjectMapper mapper = new ObjectMapper();

        mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, true);

        try {

            ProviderId providerId = new ProviderId("provider.scheme", "provider.id");
            Routes routes = mapper.readValue(stream, Routes.class);

            for (Route route : routes.getPaths()) {

                HostId srcId = route.getSrcId();
                HostId dstId = route.getDstId();
                List<DeviceId> deviceIds = route.getDeviceIds();

                submitPathIntent(providerId, deviceIds, srcId, dstId);

            }

            ObjectNode rootNode = mapper.createObjectNode();
            rootNode.put("response", "OK");
            return ok(rootNode).build();

        } catch (Exception e) {
            return Response
                    .status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity(e.toString())
                    .build();
        }

    }

    private void submitPathIntent(ProviderId providerId, List<DeviceId> deviceIds, HostId srcId, HostId dstId) {

        HostService hostService = get(HostService.class);
        PathService pathService = get(PathService.class);
        IntentService intentService = get(IntentService.class);
        CoreService coreService = get(CoreService.class);

        List<Link> links = new ArrayList<>();

        EdgeLink srcLink = new DefaultEdgeLink(providerId, new ConnectPoint((ElementId) srcId, PortNumber.portNumber(0)), hostService.getHost(srcId).location(),true);
        links.add(srcLink);

        int deviceNum = deviceIds.size();
        for (int i = 0; i < deviceNum - 1; i++) {
            links.addAll(pathService
                    .getPaths(deviceIds.get(i), deviceIds.get(i + 1))
                    .iterator()
                    .next()
                    .links()
            );
        }

        EdgeLink dstLink = new DefaultEdgeLink(providerId, new ConnectPoint((ElementId) dstId, PortNumber.portNumber(0)), hostService.getHost(dstId).location(),false);
        links.add(dstLink);

        int priority = 1;

        // set priority of this path intent the same as the existing one
        ApplicationId appId = coreService.registerApplication("org.foo.path");
        Key key = Key.of("Path(" + srcId.toString() + dstId.toString() + ")", appId);
        PathIntent pathIntent = (PathIntent) intentService.getIntent(key);
        if(pathIntent != null) {

            priority = pathIntent.priority();

            // remove the existing one
            intentService.withdraw(pathIntent);
            intentService.purge(pathIntent);
        }

        // set priority of this path intent higher than host to host intent which builds shortest path
        ApplicationId h2hAppId = coreService.registerApplication("org.onosproject.ifwd");
        Key h2hIntentKey;
        if(srcId.toString().compareTo(dstId.toString()) < 0) {
            h2hIntentKey= Key.of(srcId.toString() + dstId.toString(), h2hAppId);
        } else {
            h2hIntentKey = Key.of( dstId.toString() + srcId.toString(), h2hAppId);
        }
        HostToHostIntent h2hIntent = (HostToHostIntent) intentService.getIntent(h2hIntentKey);
        if(h2hIntent != null && intentService.getIntentState(h2hIntentKey) == IntentState.INSTALLED) {
            priority = h2hIntent.priority() + 1;
        }

        pathIntent = PathIntent.builder()
                .path( new DefaultPath(providerId, links, ScalarWeight.toWeight(1)))
                .appId(appId)
                .key(key)
                .priority(priority)
                .selector(DefaultTrafficSelector.emptySelector())
                .treatment(DefaultTrafficTreatment.emptyTreatment())
                .build();

        intentService.submit(pathIntent);

    }

}

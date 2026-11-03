package lab.owbridge;

import com.google.gson.*;
import com.sun.net.httpserver.*;
import net.fabricmc.api.ClientModInitializer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicReference;

/** First-slice diagnostic telemetry; never modifies Minecraft world state. */
public final class BridgeClient implements ClientModInitializer {
    private static final Gson JSON = new Gson();
    private final AtomicReference<Snapshot> latest = new AtomicReference<>();
    private record Snapshot(JsonObject pose, long receivedAt) {}

    @Override public void onInitializeClient() {
        try {
            HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 32131), 8);
            server.createContext("/health", this::health);
            server.createContext("/v1/pose", this::pose);
            server.start();
            Runtime.getRuntime().addShutdownHook(new Thread(() -> server.stop(0), "owbridge-stop"));
            System.out.println("[OWBridge] Diagnostic protocol 1 ready on 127.0.0.1:32131");
        } catch (IOException error) {
            System.err.println("[OWBridge] Diagnostic listener disabled: " + error.getMessage());
        }
    }

    private void health(HttpExchange request) throws IOException {
        if (!route(request, "/health", "GET")) return;
        JsonObject result = new JsonObject();
        result.addProperty("schemaVersion", 1);
        result.addProperty("host", "minecraft-fabric-1.21.1");
        Snapshot current = latest.get();
        result.addProperty("stale", current == null || System.nanoTime() - current.receivedAt > 500_000_000L);
        if (current != null) {
            result.add("latest", current.pose);
            result.addProperty("ageMs", (System.nanoTime() - current.receivedAt) / 1_000_000);
        }
        reply(request, 200, JSON.toJson(result));
    }

    private void pose(HttpExchange request) throws IOException {
        if (!route(request, "/v1/pose", "POST")) return;
        byte[] body = request.getRequestBody().readNBytes(16_385);
        if (body.length > 16_384) { reply(request, 413, "{\"error\":\"too_large\"}"); return; }
        try {
            JsonObject input = JsonParser.parseString(new String(body, StandardCharsets.UTF_8)).getAsJsonObject();
            if (integer(input.get("schemaVersion")) != 1 || integer(input.get("sequence")) < 0)
                throw new IllegalArgumentException();
            JsonElement source = input.get("source");
            if (source == null || !source.isJsonPrimitive() || !source.getAsJsonPrimitive().isString()
                    || !(source.getAsString().equals("prometheus") || source.getAsString().equals("synthetic")))
                throw new IllegalArgumentException();
            JsonObject position = input.getAsJsonObject("position");
            JsonObject coordinates = new JsonObject();
            for (String axis : new String[]{"x", "y", "z"}) {
                JsonElement value = position.get(axis);
                if (value == null || !value.isJsonPrimitive() || !value.getAsJsonPrimitive().isNumber())
                    throw new IllegalArgumentException();
                double number = value.getAsDouble();
                if (!Double.isFinite(number) || Math.abs(number) > 10_000_000) throw new IllegalArgumentException();
                coordinates.addProperty(axis, number);
            }
            JsonObject snapshot = new JsonObject();
            snapshot.addProperty("schemaVersion", 1);
            snapshot.add("source", source);
            snapshot.addProperty("sequence", integer(input.get("sequence")));
            snapshot.add("position", coordinates);
            latest.set(new Snapshot(snapshot, System.nanoTime()));
            reply(request, 200, "{\"received\":true}");
        } catch (RuntimeException invalid) {
            reply(request, 400, "{\"error\":\"invalid_pose\"}");
        }
    }

    private static long integer(JsonElement value) {
        if (value == null || !value.isJsonPrimitive() || !value.getAsJsonPrimitive().isNumber())
            throw new IllegalArgumentException();
        return value.getAsBigDecimal().longValueExact();
    }

    private static boolean route(HttpExchange request, String path, String method) throws IOException {
        if (!request.getRequestURI().getPath().equals(path)) { reply(request, 404, "{}"); return false; }
        if (!request.getRequestMethod().equals(method)) { reply(request, 405, "{}"); return false; }
        return true;
    }

    private static void reply(HttpExchange request, int status, String text) throws IOException {
        byte[] bytes = text.getBytes(StandardCharsets.UTF_8);
        request.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
        request.sendResponseHeaders(status, bytes.length);
        try (var output = request.getResponseBody()) { output.write(bytes); }
        request.close();
    }
}

package lab.owmcguest;

import java.nio.file.Path;

/** Paths supplied by tools/modpack/config.py through launch-time JVM properties.
 * Legacy fallbacks only support existing standalone fixtures/dev entry points. */
final class PrivateAssetPaths {
    private PrivateAssetPaths() {}
    static Path assets() {
        return configured("owmc.privateAssetsDirectory",
            Path.of(System.getProperty("user.home"), ".universal-modder", "assets"));
    }
    static Path meshes() {
        return configured("owmc.meshDirectory", assets().resolve("owmc-mesh"));
    }
    static Path voices() {
        String profile = System.getenv("USERPROFILE");
        Path legacy = Path.of(profile == null || profile.isBlank() ? System.getProperty("user.home") : profile,
                              ".universal-modder", "assets", "ow1-zhcn-2016", "thnu-full");
        return configured("owmc.heroVoiceDirectory", System.getProperty("owmc.privateAssetsDirectory") == null
            ? legacy : assets().resolve("ow1-zhcn-2016/thnu-full"));
    }
    private static Path configured(String property, Path fallback) {
        String value = System.getProperty(property);
        return (value == null || value.isBlank() ? fallback : Path.of(value)).toAbsolutePath().normalize();
    }
}

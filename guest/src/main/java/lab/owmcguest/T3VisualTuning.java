package lab.owmcguest;
/** User-requested presentation factors. No gameplay damage/radius/speed values. */
public final class T3VisualTuning {
    public static final float RIVET_SCALE=1.8f,PELLET_SCALE=.81f,TURRET_SCALE=1.8f,FIRE_SCALE=.65f;
    public static final float VENOM_SCALE=1.6f,BLIZZARD_DRONE_SCALE=1.65f,PULSE_SCALE=1.8f;
    public static final double PULSE_FLASH_SECONDS=.18,PULSE_WAVE_SECONDS=.7,PULSE_WAVE_RADIUS=8;
    private T3VisualTuning(){}
    public static com.google.gson.JsonObject diagnostics(){
        var o=new com.google.gson.JsonObject();o.addProperty("rivetScale",RIVET_SCALE);o.addProperty("pelletScale",PELLET_SCALE);o.addProperty("turretScale",TURRET_SCALE);
        o.addProperty("rivetVisualTimeScale",TorbRivetPresentation.VISUAL_TIME_SCALE);o.addProperty("pelletVisualSpeed",TorbRivetPresentation.PELLET_VISUAL_SPEED);o.addProperty("turretVisualSpeed",TorbTurretShots.SPEED);
        o.addProperty("venomScale",VENOM_SCALE);o.addProperty("blizzardDroneScale",BLIZZARD_DRONE_SCALE);o.addProperty("blizzardAreaRadius",10);o.addProperty("pulseScale",PULSE_SCALE);o.addProperty("blueFlashSeconds",PULSE_FLASH_SECONDS);o.addProperty("blueShockwaveRadius",PULSE_WAVE_RADIUS);return o;
    }
}

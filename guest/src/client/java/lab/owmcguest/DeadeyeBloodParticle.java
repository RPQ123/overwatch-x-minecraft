package lab.owmcguest;

import net.fabricmc.fabric.api.client.particle.v1.ParticleFactoryRegistry;
import net.minecraft.client.particle.*;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.client.render.LightmapTextureManager;

/** Brief dark-red droplets remain readable in night dimensions, then fall/fade. */
final class DeadeyeBloodParticle extends SpriteBillboardParticle {
    private DeadeyeBloodParticle(ClientWorld world,double x,double y,double z,double vx,double vy,double vz,SpriteProvider sprites){
        super(world,x,y,z,vx,vy,vz);velocityX=vx;velocityY=vy;velocityZ=vz;
        maxAge=12+random.nextInt(7);scale=.08f+random.nextFloat()*.065f;
        gravityStrength=.65f;velocityMultiplier=.91f;collidesWithWorld=true;
        red=.68f+random.nextFloat()*.15f;green=.018f;blue=.012f;alpha=.9f;setSprite(sprites);
    }
    @Override protected int getBrightness(float delta){return LightmapTextureManager.MAX_LIGHT_COORDINATE;}
    @Override public ParticleTextureSheet getType(){return ParticleTextureSheet.PARTICLE_SHEET_TRANSLUCENT;}
    @Override public void tick(){super.tick();if(age>7)alpha=.9f*Math.max(0,(maxAge-age)/(float)(maxAge-7));}
    static void register(){ParticleFactoryRegistry.getInstance().register(CombatParticles.DEADEYE_BLOOD,sprites->(type,world,x,y,z,vx,vy,vz)->new DeadeyeBloodParticle(world,x,y,z,vx,vy,vz,sprites));}
}

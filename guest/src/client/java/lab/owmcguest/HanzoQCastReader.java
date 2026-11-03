package lab.owmcguest;

/** Original ultimate state stack, separately bound from the weapon's Volley76. */
final class HanzoQCastReader implements AutoCloseable {
    static {NativeSkillReader.register("hanzoQCast",new NativeSkillReader.Spec(HanzoControlProof.HERO,0x0580000000000101L,
        java.util.Map.of("cast",19,"windup",27,"recovery",28)));}
    private final NativeSkillReader reader=new NativeSkillReader("hanzoQCast");
    NativeSkillReader.State poll(HostPoseReader.Pose h,long model){return reader.poll(h,model,HanzoControlProof.HERO);}
    String error(){return reader.error;}
    @Override public void close(){reader.close();}
}

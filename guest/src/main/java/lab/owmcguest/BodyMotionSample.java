package lab.owmcguest;

/** Completed MC tick displacement for original animation; never drives MC physics. */
public final class BodyMotionSample {
    private Object owner;
    private long world,hero,model,source;
    private int tick;
    private double[] previous,velocity={0,0,0};

    public double[] observe(Object nextOwner,long nextWorld,long nextHero,long nextModel,long nextSource,
                            int nextTick,double[] position,boolean grounded){
        if(position==null||position.length!=3||nextOwner==null||nextWorld==0||nextHero==0||nextModel==0||nextSource==0){
            reset();return new double[]{0,0,0};
        }
        for(double value:position)if(!Double.isFinite(value)){reset();return new double[]{0,0,0};}
        boolean same=owner==nextOwner&&world==nextWorld&&hero==nextHero&&model==nextModel&&source==nextSource;
        // Repeated publication in one tick must not replace the measured movement with zero.
        if(same&&nextTick==tick)return velocity.clone();
        double[] result={0,0,0};
        if(same&&previous!=null&&nextTick==tick+1){
            for(int i=0;i<3;i++)result[i]=(position[i]-previous[i])*20;
            // Teleports, source gaps and large Blink/lab rebases are positions,
            // not an instruction to feed an impossible velocity into the native mover.
            for(double value:result)if(!Double.isFinite(value)||Math.abs(value)>100){result=new double[]{0,0,0};break;}
        }
        if(grounded)result[1]=0;
        owner=nextOwner;world=nextWorld;hero=nextHero;model=nextModel;source=nextSource;tick=nextTick;
        previous=position.clone();velocity=result;return result.clone();
    }
    public void reset(){owner=null;previous=null;world=hero=model=source=0;velocity=new double[]{0,0,0};}
}

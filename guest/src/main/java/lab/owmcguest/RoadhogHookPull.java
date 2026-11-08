package lab.owmcguest;

import java.util.UUID;
import lab.owmcguest.NativeShotProtocol.Vec;

/** RH3 requested MC latch: only actor death/removal/world separation cancels.
 * Native phase/lease, distance, LOS and collisions are not latch authorities.
 * Twenty bounded steps then forced arrival also handles a moving/teleported mob. */
public final class RoadhogHookPull {
    public record Actors(UUID owner,long ownerWorld,boolean ownerAlive,UUID target,long targetWorld,boolean targetAlive,boolean targetRemoved){}
    public record Step(Vec destination,boolean complete,String cancelled){}
    private final UUID owner,target;private final long world;private int steps;private boolean ended;
    public RoadhogHookPull(UUID owner,long world,UUID target){this.owner=owner;this.world=world;this.target=target;}
    public Step advance(Actors a,Vec position,Vec feet,Vec facing){
        if(ended)return null;
        String cancel=!owner.equals(a.owner())||!a.ownerAlive()?"owner-dead-or-left-world"
            :a.ownerWorld()!=world||a.targetWorld()!=world?"world-separated"
            :!target.equals(a.target())||!a.targetAlive()||a.targetRemoved()?"target-dead-or-left-world":"";
        if(!cancel.isEmpty()){ended=true;return new Step(null,false,cancel);}
        var goal=RoadhogRules.hookGoal(feet,facing);double distance=Math.sqrt(goal.subtract(position).lengthSquared());
        boolean complete=++steps>=20||distance<=1;
        if(complete)ended=true;
        return new Step(complete?goal:position.add(RoadhogRules.pullStep(position,goal)),complete,"");
    }
    public int steps(){return steps;}
}

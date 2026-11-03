package lab.owmcguest;

import java.util.ArrayDeque;
import java.util.List;

/** Bounded real-history samples; clock reversal discards the old timeline. */
public final class NativeRecallHistory {
    public record Point(long wall,double x,double y,double z,float health){}
    private final ArrayDeque<Point> points=new ArrayDeque<>();
    public void add(Point p){
        if(p==null||!Double.isFinite(p.x())||!Double.isFinite(p.y())||!Double.isFinite(p.z())||!Float.isFinite(p.health())||p.health()<=0)return;
        if(!points.isEmpty()&&p.wall()<points.getLast().wall())points.clear();
        if(!points.isEmpty()&&p.wall()==points.getLast().wall())points.removeLast();
        points.addLast(p);while(points.size()>85||(!points.isEmpty()&&p.wall()-points.getFirst().wall()>4200))points.removeFirst();
    }
    public Point previous(long now){
        Point selected=null;for(var p:points){if(p.wall()>now)break;if(selected==null||p.wall()<=now-3000)selected=p;else break;}return selected;
    }
    public List<Point> candidates(long now){var first=previous(now);if(first==null)return List.of();return points.stream().filter(p->p.wall()>=first.wall()&&p.wall()<=now).toList();}
    public int size(){return points.size();}
    public void clear(){points.clear();}
}

package lab.owmcguest;

import java.util.*;
import lab.owmcguest.NativeShotProtocol.*;
import lab.owmcguest.NativeShotSimulation.Hit;

/** Immutable, bounded histories of accepted server sweeps. Cosmetic replay only. */
public final class RoadhogPresentation {
    public record Scope(UUID owner,long world,long model,Source source){}
    public record Segment(Vec from,Vec to,double begin,double end){}
    public record Flight(String id,long resource,long wall,long epoch,boolean instant,List<Segment> segments){}
    public record View(Scope scope,long wall,List<Flight> flights){}
    public record Sample(Vec at,Vec direction,double age,Vec trailFrom){}
    private static final class Pending {Shot shot;long epoch;List<Segment> segments=new ArrayList<>();}
    private static final Map<String,Pending> flights=new LinkedHashMap<>();private static Scope scope;
    public static volatile View view;public static long segments;
    public static volatile long shardFrames,secondaryFrames,hookFrames,chainFrames,fireFrames,trailFrames;
    public static volatile String renderError="";
    public static volatile String splitSoundStatus="{}";
    private RoadhogPresentation(){}
    private static void configure(Scope next){if(!next.equals(scope)){reset();scope=next;}}
    public static void segment(Scope next,Shot shot,Vec from,Vec to,Hit hit,double begin,double end,long now){
        if(!RoadhogRules.is(shot)||next==null)return;configure(next);
        var f=flights.get(shot.identity());
        if(f==null){if(flights.size()>=768)return;f=new Pending();f.shot=shot;f.epoch=now-Math.round(begin*1000);flights.put(shot.identity(),f);}
        if(f.segments.size()>=256)return;
        if(f.segments.isEmpty()||end>f.segments.getLast().end()){
            f.segments.add(new Segment(from,to,begin,end));segments++;
        }
    }
    public static void publish(Scope next,long now){
        configure(next);
        flights.values().removeIf(f->f.segments.isEmpty()||now-f.epoch>Math.max(0,f.shot.hitscan()?250:f.segments.getLast().end()*1000)+350);
        view=new View(scope,now,flights.values().stream().map(f->new Flight(f.shot.identity(),f.shot.effect().resource(),f.shot.wallMs(),f.epoch,f.shot.hitscan(),List.copyOf(f.segments))).toList());
    }
    public static Sample sample(Flight f,long now,long firstVisible){
        if(f==null||f.segments().isEmpty()||now<firstVisible)return null;
        double age=(now-firstVisible)/1000.;
        if(f.instant()){
            var segment=f.segments().getFirst();var d=segment.to().subtract(segment.from());double length=Math.sqrt(d.lengthSquared());
            if(length<1e-8||age>Math.min(.2,length/120)+.06)return null;
            double duration=Math.max(.025,Math.min(.2,length/120));
            return new Sample(segment.from().add(d.multiply(Math.min(1,age/duration))),d.multiply(1/length),age,
                segment.from().add(d.multiply(Math.clamp((age-.018)/duration,0,1))));
        }
        // Follow only already swept geometry, starting at the earliest received sample.
        double elapsed=f.segments().getFirst().begin()+age;var last=f.segments().getLast();
        if(elapsed>last.end()+.08)return null;
        Segment chosen=segmentAt(f,elapsed);
        var d=chosen.to().subtract(chosen.from());double length=Math.sqrt(d.lengthSquared());if(length<1e-8)return null;
        double t=Math.clamp((elapsed-chosen.begin())/Math.max(1e-8,chosen.end()-chosen.begin()),0,1);
        double prior=Math.max(f.segments().getFirst().begin(),elapsed-.018);var tail=segmentAt(f,prior);
        var trail=tail.from().add(tail.to().subtract(tail.from()).multiply(Math.clamp((prior-tail.begin())/Math.max(1e-8,tail.end()-tail.begin()),0,1)));
        return new Sample(chosen.from().add(d.multiply(t)),d.multiply(1/length),age,trail);
    }
    private static Segment segmentAt(Flight f,double elapsed){
        var chosen=f.segments().getFirst();for(var segment:f.segments()){if(elapsed>=segment.begin())chosen=segment;if(elapsed<=segment.end())break;}return chosen;
    }
    public static void reset(){flights.clear();scope=null;view=null;}
}

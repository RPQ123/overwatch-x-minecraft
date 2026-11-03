package lab.owmcguest;

/** Dependency-free native phase admission regression checks. No fixture invents native execution. */
public final class SupportNativeGateCheck {
    private static int checks;
    private static void expect(boolean ok){checks++;if(!ok)throw new AssertionError("support gate check "+checks);}
    public static void main(String[] args){
        var g=new SupportNativeGate();
        expect(g.sample(100,true,false)==SupportNativeGate.Edge.NONE&&!g.active());
        expect(g.sample(120,true,false)==SupportNativeGate.Edge.NONE&&!g.active());
        expect(g.sample(130,false,false)==SupportNativeGate.Edge.NONE);
        expect(g.sample(140,true,false)==SupportNativeGate.Edge.BEGIN&&g.active());
        expect(g.sample(140,true,false)==SupportNativeGate.Edge.NONE);
        expect(g.sample(150,true,false)==SupportNativeGate.Edge.NONE); // phase refresh is not another cast
        expect(g.sample(150,false,false)==SupportNativeGate.Edge.END&&!g.active());
        expect(g.sample(150,false,false)==SupportNativeGate.Edge.NONE);
        expect(g.sample(160,true,false)==SupportNativeGate.Edge.BEGIN);
        expect(g.sample(5,true,false)==SupportNativeGate.Edge.RESET&&!g.active());
        expect(g.sample(6,false,false)==SupportNativeGate.Edge.NONE);
        expect(g.sample(7,true,false)==SupportNativeGate.Edge.BEGIN);
        g.clear();expect(!g.active());
        expect(g.sample(7,true,false)==SupportNativeGate.Edge.NONE); // interrupted active sample cannot restart support
        var p=new SupportNativeGate();
        expect(p.sample(0,false,true)==SupportNativeGate.Edge.NONE);
        expect(p.sample(10,false,true)==SupportNativeGate.Edge.PULSE);
        expect(p.sample(10,false,true)==SupportNativeGate.Edge.NONE);
        expect(p.sample(20,true,true)==SupportNativeGate.Edge.NONE);
        expect(p.sample(20,false,true)==SupportNativeGate.Edge.PULSE);
        expect(p.sample(21,false,true)==SupportNativeGate.Edge.PULSE);
        p.clear();expect(p.sample(30,true,true)==SupportNativeGate.Edge.NONE);
        expect(p.sample(31,false,true)==SupportNativeGate.Edge.NONE); // old volley ending after baseline is not a new shot
        expect(p.sample(40,false,true)==SupportNativeGate.Edge.PULSE);
        expect(p.sample(-1,false,true)==SupportNativeGate.Edge.RESET);
        System.out.println("support native gate: "+checks+" checks passed; fixtureOnly=true");
    }
}

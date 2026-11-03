package lab.owmcguest;

/** Release to arm after focus/session changes; held keys never repeat toggles. */
public final class FlightToggle {
    private long generation;
    private boolean armed,down;
    public boolean poll(long session,boolean active,boolean pressed) {
        if(!active||session==0||session!=generation){generation=session;armed=false;down=pressed;return false;}
        if(!pressed){armed=true;down=false;return false;}
        boolean toggle=armed&&!down;down=true;return toggle;
    }
}

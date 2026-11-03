package lab.owmcguest;

/** Edge-triggered second jump state; it never toggles creative flight. */
public final class GenjiDoubleJump {
    private boolean previousPressed;
    private boolean armed;

    /** Call once at the start of the player movement tick. */
    public boolean tick(boolean genji, boolean active, boolean grounded, boolean pressed) {
        boolean edge = active && pressed && !previousPressed;
        boolean trigger = genji && active && edge && !grounded && armed;
        if (!genji || !active) armed = false;
        else if (grounded) armed = true;
        if (trigger) armed = false;
        previousPressed = active && pressed;
        return trigger;
    }

    public void reset() { previousPressed = false; armed = false; }
}

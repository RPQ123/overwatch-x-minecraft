package lab.owmcguest;

public final class GenjiDoubleJumpCheck {
    private static void require(boolean value) { if (!value) throw new AssertionError("Genji double jump state"); }

    public static void main(String[] args) {
        var jump = new GenjiDoubleJump();
        require(!jump.tick(true, true, true, true));  // first jump, grounded
        require(!jump.tick(true, true, false, true)); // held key is not a second jump
        require(!jump.tick(true, true, false, false));
        require(jump.tick(true, true, false, true));  // released, then pressed in air
        require(!jump.tick(true, true, false, false));
        require(!jump.tick(false, true, false, true)); // hero switch disables it
        require(!jump.tick(true, true, false, false)); // no stale arm after switch
        require(!jump.tick(true, true, true, true));   // grounded press arms only
        System.out.println("PASS: Genji-only released-edge double jump, no flight toggle");
    }
}

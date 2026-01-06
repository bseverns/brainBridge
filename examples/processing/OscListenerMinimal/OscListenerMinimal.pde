import oscP5.*;
import netP5.*;

OscP5 osc;
float energy = 0.0;
String scene = "none";

void setup() {
  size(640, 360);
  osc = new OscP5(this, 9003);
  textSize(16);
}

void draw() {
  background(0);
  fill(255);
  text("scene: " + scene, 20, 40);
  text("energy: " + nf(energy, 1, 3), 20, 70);
  rect(20, 100, energy * (width - 40), 20);
}

void oscEvent(OscMessage msg) {
  println(msg.addrPattern() + " " + msg.typetag() + " " + msg.arguments());

  if (msg.addrPattern().equals("/rig/energy") && msg.arguments().length > 0) {
    energy = msg.get(0).floatValue();
  }
  if (msg.addrPattern().equals("/rig/scene") && msg.arguments().length > 0) {
    scene = msg.get(0).stringValue();
  }
}

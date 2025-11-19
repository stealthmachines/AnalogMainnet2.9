
uniform float time;
varying vec3 vColor;

void main() {
    vColor = vec3(position.x + 0.5, position.y + 0.5, sin(time) * 0.5 + 0.5);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
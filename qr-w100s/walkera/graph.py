from vispy import gloo
from vispy import app
from vispy import scene
import numpy as np
import math
import threading
from walkera.video_lk import Video
from vispy.scene.visuals import Text

# Number of cols and rows in the table.
nrows = 2
ncols = 1

# Number of signals.
m = nrows*ncols

# Number of samples per signal.
n = 1000

# Various signal amplitudes.
amplitudes = .1# + .2 * np.random.rand(m, 1).astype(np.float32)

# Generate the signals as a (m, n) array.
y = amplitudes * np.random.randn(m, n).astype(np.float32)

# Color of each vertex (TODO: make it more efficient by using a GLSL-based
# color map and the index).
color = np.repeat(np.random.uniform(size=(m, 3), low=.5, high=.9),
                  n, axis=0).astype(np.float32)

# Signal 2D index of each vertex (row and col) and x-index (sample index
# within each signal).
index = np.c_[np.repeat(np.repeat(np.arange(ncols), nrows), n),
              np.repeat(np.tile(np.arange(nrows), ncols), n),
              np.tile(np.arange(n), m)].astype(np.float32)



VERT_SHADER = """
#version 120

// y coordinate of the position.
attribute float a_position;

// row, col, and time index.
attribute vec3 a_index;
varying vec3 v_index;

// 2D scaling factor (zooming).
uniform vec2 u_scale;

// Size of the table.
uniform vec2 u_size;

// Number of samples per signal.
uniform float u_n;

// Color.
attribute vec3 a_color;
varying vec4 v_color;

// Varying variables used for clipping in the fragment shader.
varying vec2 v_position;
varying vec4 v_ab;

void main() {
    float nrows = u_size.x;
    float ncols = u_size.y;

    // Compute the x coordinate from the time index.
    float x = -1 + 2*a_index.z / (u_n-1);
    vec2 position = vec2(x, a_position);

    // Find the affine transformation for the subplots.
    vec2 a = vec2(1./ncols, 1./nrows)*.9;
    vec2 b = vec2(-1 + 2*(a_index.x+.5) / ncols,
                  -1 + 2*(a_index.y+.5) / nrows);
    // Apply the static subplot transformation + scaling.
    gl_Position = vec4(a*u_scale*position+b, 0.0, 1.0);

    v_color = vec4(a_color, 1.);
    v_index = a_index;

    // For clipping test in the fragment shader.
    v_position = gl_Position.xy;
    v_ab = vec4(a, b);
}
"""

FRAG_SHADER = """
#version 120

varying vec4 v_color;
varying vec3 v_index;

varying vec2 v_position;
varying vec4 v_ab;

void main() {
    gl_FragColor = v_color;

    // Discard the fragments between the signals (emulate glMultiDrawArrays).
    if ((fract(v_index.x) > 0.) || (fract(v_index.y) > 0.))
        discard;

    // Clipping test.
    vec2 test = abs((v_position.xy-v_ab.zw)/v_ab.xy);
    if ((test.x > 1) || (test.y > 1))
        discard;
}
"""


class Canvas(scene.SceneCanvas):
    def __init__(self, video=None):
        scene.SceneCanvas.__init__(self, title='Use your wheel to zoom!',
                            keys='interactive')
        self.program = gloo.Program(VERT_SHADER, FRAG_SHADER)
        self.program['a_position'] = y.reshape(-1, 1)
        self.program['a_color'] = color
        self.program['a_index'] = index
        self.program['u_scale'] = (1., 1.)
        self.program['u_size'] = (nrows, ncols)
        self.program['u_n'] = n

        self.counter = 0
        self.video = video

        # dir(gloo)
        # t1 = Text('Text in root scene (24 pt)', parent=gloo, color='red')
        # t1.font_size = 24
        # t1.pos = self.size[0] // 2, self.size[1] // 3
        # self.draw_visual(t1)

        #self._timer = app.Timer('auto', connect=self.on_timer, start=True)



    def on_initialize(self, event):
        gloo.set_state(clear_color='black', blend=True,
                       blend_func=('src_alpha', 'one_minus_src_alpha'))

    def on_resize(self, event):
        self.width, self.height = event.size
        gloo.set_viewport(0, 0, self.width, self.height)

    def on_mouse_wheel(self, event):
        dx = np.sign(event.delta[1]) * .05
        scale_x, scale_y = self.program['u_scale']
        scale_x_new, scale_y_new = (scale_x * math.exp(2.5*dx),
                                    scale_y * math.exp(0.0*dx))
        self.program['u_scale'] = (max(1, scale_x_new), max(1, scale_y_new))
        self.update()

    def add_points(self,data0,data1):
        k = 5
        y[:, :-k] = y[:, k:]
        print "data data", data0, data1
        y[0, -k:] = data0
        y[1, -k:] = data1
        
        self.counter+=1
        self.program['a_position'].set_data(y.ravel().astype(np.float32))
        self.update()

    
    def on_timer(self, event):
        """Add some data at the end of each signal (real-time signals)."""
        k = 5
        highLatency = 150
        standardDev = 100
        y[:, :-k] = y[:, k:]
        if self.video != None:
            # Latency Graph
            y[0, -k:] = (self.video.getLatency()-highLatency)/standardDev
            print self.video.getLatency()
            # Graph
            y[1, -k:] = (self.counter/100.)%2-1

        else:
            y[:, -k:] = amplitudes * np.random.randn(m, k)
        self.counter+=1
        self.program['a_position'].set_data(y.ravel().astype(np.float32))
        self.update()

    def on_draw(self, event):
        gloo.clear()
        self.program.draw('line_strip')

    def startThread(self):
        self.myThread = threading.Thread(target=app.run)
        self.myThread.start()

if __name__ == '__main__':
    c = Canvas()

    vb = scene.widgets.ViewBox(parent=c.scene, border_color='b')
    vb.pos = 0, c.size[1] // 2
    vb.size = c.size[0], c.size[1] // 2
    # vb.camera.rect = 0, 0, canvas.size[0], canvas.size[1] // 2
    vb.camera.rect = 0, 0, 1, 1
    vb.camera.rect = -200, -100, 400, 200
    vb.camera.invert_y = False
    # vb.clip_method = None
    t2 = Text('Text in root scene (24 pt)', parent=vb.scene, color='red')
    # print dir(t2)

    t2.font_size = 100
    t2.pos = c.size[0] // 2, c.size[1] // 3
    # c.draw_visual(t2)
    # t2.draw(c.scene)
    # print dir(c.canvas_cs)
    # print c.scene, c.size, t2
    c.show()
    app.run()
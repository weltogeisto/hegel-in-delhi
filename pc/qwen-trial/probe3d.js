// The probe for Welt's 3D test (pc/qwen-trial/scene3d.json). render3d.py puts it first in the model's page; the
// model never sees it. It samples the scene at 1, 2 and 3 seconds, right after a frame is drawn, and writes what
// it saw as JSON into a hidden pre element, which the headless browser's --dump-dom prints.
// The browser dumps (or takes its screenshot) at the page's load event. Headless frames only run in real time, so
// the probe holds the load event open with an image that the loopback server sends after ?wait= milliseconds.
(function () {
  'use strict';
  var SAMPLES = [1000, 2000, 3000], FINAL_MS = 3600;
  var NAMES = ['sun', 'planet1', 'planet2', 'planet3', 'moon'];
  var errors = [], samples = [], next = 0, done = false, first = null, frames = 0, t0 = performance.now();
  var wait = +(new URLSearchParams(location.search).get('wait') || 3900);
  var hold = document.createElement('img');
  hold.style.display = 'none';
  hold.src = '/__wait?ms=' + wait;
  document.documentElement.appendChild(hold);

  function note(kind, msg) { if (errors.length < 20) errors.push(kind + ': ' + String(msg).slice(0, 300)); }
  window.addEventListener('error', function (e) {
    var el = e.target;
    if (el === hold) return;
    if (el && el !== window && el.tagName) note('resource', el.src || el.href || el.tagName);
    else note('error', (e.error && e.error.stack) || e.message);
  }, true);
  window.addEventListener('unhandledrejection', function (e) {
    var r = e.reason; note('rejection', (r && (r.stack || r.message)) || r);
  });
  var consoleError = console.error;
  console.error = function () {
    note('console', Array.prototype.map.call(arguments, String).join(' '));
    return consoleError.apply(console, arguments);
  };

  // Every animation frame the page asks for runs as before; the probe looks right after it, while the frame's
  // pixels are still in the WebGL drawing buffer.
  var raf = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = function (cb) {
    return raf(function (ts) { try { cb(ts); } finally { after(); } });
  };

  function after() {
    frames++;
    if (done || next >= SAMPLES.length) return;
    var t = performance.now() - t0;
    if (t < SAMPLES[next]) return;
    try { samples.push(sample(t)); } catch (e) { samples.push({ t: Math.round(t), err: String(e).slice(0, 200) }); }
    next++;
    if (next === SAMPLES.length) finish('samples');
  }
  setTimeout(function () { finish('timeout'); }, FINAL_MS);

  function find(scene, name) {           // a mesh of that name if there is one, else the first object of that name
    var hits = [];
    scene.traverse(function (o) { if (o.name === name) hits.push(o); });
    for (var i = 0; i < hits.length; i++) if (hits[i].isMesh) return hits[i];
    return hits[0] || null;
  }
  function wpos(o) { var e = o.matrixWorld.elements; return [e[12], e[13], e[14]]; }
  function biggestCanvas() {
    var best = null, area = -1;
    Array.prototype.forEach.call(document.querySelectorAll('canvas'), function (c) {
      var r = c.getBoundingClientRect(); if (r.width * r.height > area) { area = r.width * r.height; best = c; }
    });
    return best;
  }
  function glows(o) {
    var m = null;
    o.traverse(function (c) { if (!m && c.isMesh) m = c; });
    if (!m) return false;
    var mat = Array.isArray(m.material) ? m.material[0] : m.material;
    if (!mat) return false;
    if (mat.isMeshBasicMaterial || mat.isShaderMaterial || mat.isRawShaderMaterial) return true;
    var em = mat.emissive;
    return !!(em && (em.r + em.g + em.b) > 0 && !(mat.emissiveIntensity <= 0));
  }
  function pixels(cv, s) {
    try {
      var c = document.createElement('canvas'); c.width = cv.width; c.height = cv.height;
      var g = c.getContext('2d'); g.drawImage(cv, 0, 0);
      var d = g.getImageData(0, 0, c.width, c.height).data, n = c.width * c.height, bins = new Uint32Array(4096), i;
      for (i = 0; i < d.length; i += 4) bins[((d[i] >> 4) << 8) | ((d[i + 1] >> 4) << 4) | (d[i + 2] >> 4)]++;
      var modal = 0; for (i = 1; i < 4096; i++) if (bins[i] > bins[modal]) modal = i;
      s.nonModal = n ? (n - bins[modal]) / n : 0;
      if (!first) first = d;
      else if (first.length === d.length) {
        var changed = 0;
        for (i = 0; i < d.length; i += 4) {
          if (Math.abs(d[i] - first[i]) + Math.abs(d[i + 1] - first[i + 1]) + Math.abs(d[i + 2] - first[i + 2]) > 24) changed++;
        }
        s.changedVsFirst = changed;
      }
    } catch (e) { s.pixelErr = String(e).slice(0, 200); }
  }

  function sample(t) {
    var s = { t: Math.round(t), win: [innerWidth, innerHeight] };
    var scene = window.scene, cam = window.camera;
    s.scene = !!(scene && scene.isScene);
    s.camera = !!(cam && cam.isCamera);
    var cv = biggestCanvas();
    if (cv) {
      var r = cv.getBoundingClientRect();
      s.canvas = [r.left, r.top, r.width, r.height, cv.width, cv.height];
      pixels(cv, s);
    }
    if (!s.scene) return s;
    scene.updateMatrixWorld(true);
    s.pos = {};
    var named = [], objs = {};
    NAMES.forEach(function (n) {
      var o = find(scene, n);
      if (o) { objs[n] = o; s.pos[n] = wpos(o); o.traverse(function (c) { named.push(c); }); }
    });
    s.lights = []; s.stars = 0;
    scene.traverse(function (o) {
      if (o.isPointLight) s.lights.push(wpos(o));
      if (o.isPoints && o.geometry && o.geometry.attributes && o.geometry.attributes.position) {
        s.stars += o.geometry.attributes.position.count;
      } else if (o.isInstancedMesh) {
        s.stars += o.count;
      } else if (o.isMesh && named.indexOf(o) < 0) {
        s.stars += 1;
      }
    });
    s.sunGlows = objs.sun ? glows(objs.sun) : false;
    if (s.camera) {
      cam.updateMatrixWorld(true);
      s.cam = wpos(cam);
      s.aspect = cam.aspect === undefined ? null : cam.aspect;
      if (objs.sun) {
        var v = objs.sun.position.clone(), p = s.pos.sun;
        v.set(p[0], p[1], p[2]); v.project(cam);
        s.sunNdc = [v.x, v.y, v.z];
      }
    }
    return s;
  }

  function finish(why) {
    if (done) return;
    done = true;
    var out = { why: why, frames: frames, errors: errors, samples: samples };
    var pre = document.createElement('pre');
    pre.id = '__probe3d';
    pre.style.display = 'none';
    pre.textContent = JSON.stringify(out);
    (document.body || document.documentElement).appendChild(pre);
  }
})();

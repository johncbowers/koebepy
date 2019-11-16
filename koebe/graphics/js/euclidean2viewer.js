/* 
 * JavaScript to interact with p5viewer.py for viewing constructions in 
 * Jupyter
 * Based on example: https://hub.gke.mybinder.org/user/jtpio-p5-jupyter-notebook-z9kpfjdk/notebooks/puzzle.ipynb
 * @author John C. Bowers
 */ 


/*** LIBRARIES ***/
require.config({
    paths: {
        'p5': 'https://cdnjs.cloudflare.com/ajax/libs/p5.js/0.9.0/p5.min',
        'lodash': 'https://cdnjs.cloudflare.com/ajax/libs/lodash.js/4.17.4/lodash.min'
    }
});

/*** HELPER FUNCTIONS ***/

window.defineModule = function (name, dependencies, module) {
    // force the recreation of the module
    // (when re-executing a cell)
    require.undef(name);
    
    define(name, dependencies, module);
};

window.createSketchView = function (name, dependencies, module) {
    
    require.undef(name);
    
    define(name,
           ['@jupyter-widgets/base', 'p5', 'lodash'].concat(dependencies),
           (widgets, p5, _, ...deps) => {

        let viewName = `${name}View`;
        
        let View = widgets.DOMWidgetView.extend({
            initialize: function () {
                this.el.setAttribute('style', 'text-align: center;');
            },

            render: function () {
                // pass the model as the last dependency so it can
                // be accessed in the sketch
                let sketch = module(...deps, this.model);
                setTimeout(() => {
                    this.sketch = new p5(sketch, this.el);                    
                }, 0);
            },

            remove: function () {
                // stop the existing sketch when the view is removed
                // so p5.js can cancel the animation frame callback and free up resources
                if (this.sketch) {
                    this.sketch.remove();
                    this.sketch = null;
                }
            }
        });
        
        return {
            [viewName] : View,
        };
    });
}

// Test module defining a few constants, for example purposes
// Such constants should ideally be defined directly in the model
// and directly accessed by the view

defineModule('euclidean2Module', [], () => {
    const [W, H] = [500, 500];
    return {W, H};
})

let _shown = false;
var THE_STYLE = 0;
var _DEBUG = false;

createSketchView('E2Sketch', ['euclidean2Module'], (Settings, model) => {
    return function(p) {
        const {W, H} = Settings;
        
        p.setup = function(){
            let w = model.get('width');
            let h = model.get('height');
            let s = model.get('scale');
            p.createCanvas(w, h);
            p.zoom = 1.0;
            p.canvasScale = s;
            p.frame = 0;
        }
        
        p.setStyle = function(style) {
            
            if (style == null) return;

            if ("stroke" in style) {
                if (style["stroke"] == null) p.noStroke();
                else                         p.stroke(style["stroke"]);
            }
            
            if ("strokeWeight" in style) {
                if (style["strokeWeight"] != null) p.strokeWeight(style["strokeWeight"]*p.canvasScale);
            }
            
            if ("fill" in style) {
                if (style["fill"] == null) p.noFill();
                else                       p.fill(style["fill"]);
            }
        }
        
        p.hasStyle = function (objData) {
            return "style" in objData && objData["style"] != null;
        }
        
        p.drawPointE2 = function (pointData) {
            let pt = pointData["point"];
            if (!p.hasStyle(pointData)) {
                p.noStroke();
                p.fill(100, 125, 255);
            }
            p.circle(pt[0], pt[1], 5 * p.canvasScale);
        }
        
        p.drawPolygon = function(polygonData) {
            let polygon = polygonData["vertices"];
            p.beginShape();
            polygon.forEach(v => {
                p.vertex(v[0], v[1]);
            });
            p.endShape();
        }
        
        p.drawPolygons = function (polygonsData) {
            let polygons = polygonsData["polygons"];
            polygons.forEach(polygon => {
                p.beginShape();
                polygon.forEach(v => {
                    p.vertex(v[0], v[1]);
                });
                p.endShape();
            });
        }
        
        p.drawCircleE2 = function (circleData) {
            let center = circleData["center"];
            let radius = circleData["radius"];
            if (!p.hasStyle(circleData)) {
                p.stroke(0,0,0);
                p.noFill();
            }
            p.circle(center[0], center[1], 2*radius);
        }
        
        p.drawSegmentE2 = function (segData) {
            let endpoints = segData["endpoints"];
            p.line(endpoints[0][0],
                   endpoints[0][1],
                   endpoints[1][0],
                   endpoints[1][1]);
        }
        
        p.drawCircleArcE2 = function (arcData) {
            let center = arcData["center"];
            let radius = arcData["radius"];
            let srcAngle = arcData["srcAngle"];
            let targetAngle = arcData["targetAngle"];
            let diameter = 2 * radius;
            
            p.arc(center[0], center[1], diameter, diameter, srcAngle, targetAngle);
        }
/*
"center": arc.disk.center.toPointE2(), 
                      "radius": rad,
                      "srcAngle": srcAngle, 
                      "targetAngle": targetAngle}
                      */
        p.draw = function () {
            
            if (model.get('objectsDirty') || p.objs.length > 1) {
                model.set('objectsDirty', false);
                p.objs = JSON.parse(model.get('objects'));
                
                
                p.scale(1 / p.canvasScale, -1 / p.canvasScale);
                p.translate(p.canvasScale * p.width * 0.5, -p.canvasScale * p.height * 0.5);
                
            
                p.background('#fff');

                p.objs[p.frame].forEach(obj => {
                    p.push();
                    if ("style" in obj && obj["style"] != null) {
                        p.setStyle(obj["style"]);
                    }
                    switch (obj["type"]) {
                        case "PointE2": p.drawPointE2(obj); break;
                        case "Polygons": p.drawPolygons(obj); break;
                        case "Polygon": p.drawPolygon(obj); break;
                        case "SegmentE2": p.drawSegmentE2(obj); break;
                        case "CircleE2": p.drawCircleE2(obj); break;
                        case "CircleArcE2": p.drawCircleArcE2(obj); break;
                        default: console.log(obj["type"] + " is not drawable in this sketch.");
                    }
                    p.pop();
                });
                if (p.objs.length == 1) {
                    p.noLoop();
                } else {
                    p.frame = (p.frame + 1) % p.objs.length;
                }
            }
            
        }
        
        p.keyTyped = function () {
          if (key === 'e') {
            photo.save('photo', 'png');
          }
        }
    };
})
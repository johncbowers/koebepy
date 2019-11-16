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

defineModule('testModule', [], () => {
    const [W, H] = [500, 500];
    return {W, H};
})

let _shown = false;
var THE_STYLE = 0;
var _DEBUG = true;

createSketchView('S2Sketch', ['testModule'], (Settings, model) => {
    return function(p) {
        const {W, H} = Settings;
        
        p.setup = function(){
            let w = model.get('width');
            let h = model.get('height');
            p.createCanvas(w, h, p.WEBGL);
            p.zoom = 1.0;
            p.frame = 0;
        }
        
        p.setStyle = function(style) {
            
            if (style == null) return;

            if ("stroke" in style) {
                if (style["stroke"] == null) p.noStroke();
                else                         p.stroke(style["stroke"]);
            }
            
            if ("strokeWeight" in style) {
                if (style["strokeWeight"] != null) p.strokeWeight(style["strokeWeight"]);
            }
            
            if ("fill" in style) {
                if (style["fill"] == null) p.noFill();
                else                       p.fill(style["fill"]);
            }
        }
        
        p.hasStyle = function (objData) {
            return "style" in objData && objData["style"] != null;
        }
        
        p.drawPointE3 = function (pointData) {
            let pt = pointData["point"];
            p.translate(pt[0], pt[1], pt[2]);
            if (!p.hasStyle(pointData)) {
                p.noStroke();
                p.fill(100, 125, 255);
            }
            //p.sphereDetail(2);
            //p.sphere(0.035, 8, 8);
            p.box(0.035);
        }
        
        p.drawDiskS2 = function (diskData) {
            
            
            let disk = diskData["disk"];
            
            let b1 = diskData["b1"];
            let b2 = diskData["b2"];
            let b3 = diskData["b3"];
            
            let centerDist = diskData["centerDist"];
            let diameter = diskData["diameter"];
           
            // This code works in processing 3 but p5.js appears to want the
            // transpose for some reason: 
//             p.applyMatrix(
//                 b1[0], b2[0], b3[0], 0,
//                 b1[1], b2[1], b3[1], 0,
//                 b1[2], b2[2], b3[2], 0,
//                 0, 0, 0, 1
//             );
            
            // THIS HACK MAKES IT WORK IN p5.js
            // BUT THE CORRECT CODE IS ABOVE.
            p.applyMatrix(
                b1[0], b1[1], b1[2], 0,
                b2[0], b2[1], b2[2], 0,
                b3[0], b3[1], b3[2], 0,
                0, 0, 0, 1
            );
            
//             if (_DEBUG) {
//                 console.log("applying matrix\n" +       
//                     b1[0] + " " + b2[0] + " " + b3[0] + " " + 0 + "\n" + 
//                     b1[1] + " " + b2[1] + " " + b3[1] + " " + 0 + "\n" + 
//                     b1[2] + " " + b2[2] + " " + b3[2] + " " + 0 + "\n" + 
//                     "0 0 0 1"
//                 );
//             }
            
            if (disk[3] < 0) {
//                 if (_DEBUG) console.log("translate " + centerDist);
                p.translate(0, 0,  centerDist);
            } else {
//                 if (_DEBUG) console.log("translate " + (-centerDist));
                p.translate(0, 0, -centerDist);
            }
            
            if (!p.hasStyle(diskData)) {
                p.strokeWeight(4);
                p.stroke(0);
            }
            p.ellipse(0, 0, diameter, diameter, 48);
            
        }
        
        p.drawPolygon = function(polygonData) {
            let polygon = polygonData["vertices"];
            p.beginShape();
            polygon.forEach(v => {
                p.vertex(v[0], v[1], v[2]);
            });
            p.endShape();
        }
        
        p.drawPolygons = function (polygonsData) {
            let polygons = polygonsData["polygons"];
            polygons.forEach(polygon => {
                p.beginShape();
                polygon.forEach(v => {
                    p.vertex(v[0], v[1], v[2]);
                });
                p.endShape();
            });
        }
        
        p.drawSegmentE3 = function (segData) {
            let endpoints = segData["endpoints"];
            p.line(endpoints[0][0],
                   endpoints[0][1],
                   endpoints[0][2],
                   endpoints[1][0],
                   endpoints[1][1],
                   endpoints[1][2]);
        }

        p.draw = function () {
            
            if (model.get('objectsDirty')) {
                model.set('objectsDirty', false);
                p.objs = JSON.parse(model.get('objects'));
            }
            
            p.background('#fff');
            
            p.orbitControl(5, 5);
            //p.translate(p.width / 2.0, p.height / 2.0, 0.0);
            p.scale(1.0, -1.0, 1.0);
            p.scale(200 * p.zoom);
            p.strokeWeight(0.005 / p.zoom);
            
            //p.pushStyle();
            p.noStroke();
            p.lights();
            //p.sphereDetail(200);
            //p.sphereDetail(30);
            if (model.get('showSphere'))
                p.sphere(0.999, 96, 64);
            //p.sphereDetail(30);
            
            p.objs[p.frame].forEach(obj => {
                p.push();
                if ("style" in obj && obj["style"] != null) {
                    p.setStyle(obj["style"]);
                }
                switch (obj["type"]) {
                    case "DiskS2": p.drawDiskS2(obj); break;
                    case "PointE3": p.drawPointE3(obj); break;
                    case "Polygons": p.drawPolygons(obj); break;
                    case "Polygon": p.drawPolygon(obj); break;
                    case "SegmentE3": p.drawSegmentE3(obj); break;
                    default: console.log(obj["type"] + " is not drawable in this sketch.");
                }
                p.pop();
            });
            
            if (p.objs.length != 1) {
                p.frame = (p.frame + 1) % p.objs.length;
            }
        } 
    };
})
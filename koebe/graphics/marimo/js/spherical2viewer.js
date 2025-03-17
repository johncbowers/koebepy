window.createSketchView = (model, attributes) => function (p) {
    var x = 0;
    
    p.setup = function() {
        let w = 500;
        let h = 500;
        p.createCanvas(w, h, p.WEBGL);
        p.zoom = 1;
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
        
        if (disk[3] < 0) {
            p.translate(0, 0,  centerDist);
        } else {
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
    
    p.drawVertexColoredTriangle = function(triangleData) {
        let p1 = triangleData["p1"];
        let p2 = triangleData["p2"];
        let p3 = triangleData["p3"];
        let color1 = triangleData["color1"];
        let color2 = triangleData["color2"];
        let color3 = triangleData["color3"];
        
        p.beginShape(p.TRIANGLES);
        p.fill(color1);
        p.vertex(p1[0], p1[1], p1[2]);
        p.fill(color2);
        p.vertex(p2[0], p2[1], p2[2]);
        p.fill(color3);
        p.vertex(p3[0], p3[1], p3[2]);
        p.endShape(p.CLOSE);
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

        let show_sphere = model.get("show_sphere")

        // if (model.get('objectsDirty')) {
        //     model.set('objectsDirty', false);
            p.objs = JSON.parse(model.get('objects'));
            console.log(p.objs);
        // }
        
        p.background(255, 254, 235);
        
        p.orbitControl(5, 5);
        
        p.scale(1.0, -1.0, 1.0);
        p.scale(200 * p.zoom);
        p.strokeWeight(0.005 / p.zoom);
        
        p.noStroke();

        if (show_sphere) {
            p.fill(220, 220, 220);
            p.sphere(0.999, 96, 64);
        }

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
                case "VertexColoredTriangle": p.drawVertexColoredTriangle(obj); break;
                default: console.log(obj["type"] + " is not drawable in this sketch.");
            }
            p.pop();
        });
        
        if (p.objs.length != 1) {
            p.frame = (p.frame + 1) % p.objs.length;
        }
    }
}


function render({ model, el }) {
    
    let scriptEl = document.createElement("script");
    scriptEl.src = "https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.11.2/p5.min.js";
    
    
    scriptEl.onload = function () {
    
        let canvasContainerElem = document.createElement("div");
        el.appendChild(canvasContainerElem);

        let attributes = {"objects":JSON.parse(model.get("objects"))}
        let sketchView = window.createSketchView(model, attributes);

        var sketch; 

        setTimeout(() => {
            sketch = new p5(sketchView, canvasContainerElem);  
            canvasContainerElem.children[0].style.height = "1px";  
            canvasContainerElem.children[1].style.visibility = "visible";  
        }, 10);

        // model.on("change:objects", () => {
        //     attributes["objects"] = JSON.parse(model.get("objects"));
        // });
    
        // For some reason, though this happens automatically in p5 when not 
        // in marimo, it has to be done manually here. 
        
    }

    document.documentElement.firstChild.appendChild(scriptEl);

    return function() {
        sketch.remove();
    }
}
export default { render };
/* 
    Author : Islam Akef Ebeid
    Affiliations : University of Arkansas at Little Rock - Emerging Analytics Center
*/

function Point(x, y) {
    this.x = x;
    this.y = y;
    this.getInfo = function () {
        return this.x + "," + this.y;
    };
}



function Layout(id) {
    var unit = 16.18;
    var viewPortWidth = $("#" + id).width();
    var viewPortHeight = $("#" + id).height();
    var div = d3.select("#" + id);
    var svg = div.append("svg").attr("id", "draw")
            .attr("width", "100%")
            .attr("height", "100%")
            .attr("viewBox", "0 0 " + viewPortWidth + " " + viewPortHeight)
            .attr("preserveAspectRatio", "xMinYMin meet");
    
        var vis = $("#draw"),
    aspect = vis.width() / vis.height(),
    container = vis.parent();
    var targetWidth = container.width();
    vis.attr("width", targetWidth);
    vis.attr("height", Math.round(targetWidth / aspect));

        
    this.constructViewPortMatrix = function () {
        var matrix = [];
        var numberOfPointsInXDir = viewPortWidth / unit;
        var numberOfPointsInYDir = viewPortHeight / unit;
        for (var x = 0; x < numberOfPointsInXDir; x++) {
            matrix[x] = [];
            for (var y = 0; y < numberOfPointsInYDir; y++) {
                matrix[x][y] = new Point(x, y);
                this.drawPoint(matrix[x][y].x,matrix[x][y].y);
                //this.drawGrid(matrix[x][y].x,matrix[x][y].y);
            }
        }
    }
    
    this.drawPoint = function (x,y){
        var circles = svg.append("circle");
        var circleAttributes = circles
                       .attr("cx", x*unit)
                       .attr("cy", y*unit)
                       .attr("r", "1px")
                       .style("fill", "#ccc");
    }
    
    this.drawGrid = function(x,y){
        var square = svg.append("rect");
        var squareAttr = square.attr("x",x*unit).attr("y",y*unit).attr("width",50).attr("height",50).style("fill:white;stroke-width:0.1;stroke:grey;");
    }
    
    this.getSvg = function (){
        return svg;
    }
    
    this.putObjectAt = function(x,y,object){
        object.attr("transform", "translate(" + x*unit + "," + y*unit + ")");
    }
}
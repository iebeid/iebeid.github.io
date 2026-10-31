/* 
    Author : Islam Akef Ebeid
    Affiliations : University of Arkansas at Little Rock - Emerging Analytics Center
*/

function makeLegend(data, color, positionX, positionY, barWidthInput, barHeightInput, orientation, groupName, unit, fontSize) {
    var x1 = positionX;
    var barWidth = barWidthInput;
    var y1 = positionY;
    var barHeight = barHeightInput;
    var numberHues = data.length;
    var idGradient = groupName+"legendGradient";
    var gradientDirectionX = 0;
    var gradientDirectionY = 0;
    var leftLegendPositionX = 0;
    var leftLegendPositionY = 0;
    var rightLegendPositionX = 0;
    var rightLegendPositionY = 0;
    //var textY = y1 + barHeight / 2;
    var textY = y1+(barHeight/1.25);
    var hueStart = 160, hueEnd = 0;
    var opacityStart = data[0].opacityValue, opacityEnd = data[data.length - 1].opacityValue;
    var theHue, rgbString, opacity, p;
    var deltaPercent = 1 / (numberHues - 1);
    var deltaHue = (hueEnd - hueStart) / (numberHues - 1);
    var deltaOpacity = (opacityEnd - opacityStart) / (numberHues - 1);
    var theData = [];

    if (orientation === "horizontal") {
        gradientDirectionX = "100%";
        gradientDirectionY = "0%";
        leftLegendPositionX = x1-5;
        leftLegendPositionY = textY;
        rightLegendPositionX = x1 + barWidth;
        rightLegendPositionY = textY;
    }
    else if (orientation === "vertical") {
        gradientDirectionX = "0%";
        gradientDirectionY = "100%"
        leftLegendPositionX = x1;
        leftLegendPositionY = y1 + barHeight + unit;
        rightLegendPositionX = x1;
        rightLegendPositionY = y1 - unit;
    }

    var svgForLegendStuff = d3.select("#" + groupName);

    svgForLegendStuff.append("g").attr("id", groupName+"LegendGroup").append("defs")
            .append("linearGradient")
            .attr("id", idGradient)
            .attr("x1", "0%")
            .attr("x2", gradientDirectionX)
            .attr("y1", gradientDirectionY)
            .attr("y2", "0%");

    svgForLegendStuff.append("rect")
            .attr("fill", "url(#" + idGradient + ")")
            .attr("x", x1)
            .attr("y", y1)
            .attr("width", barWidth)
            .attr("height", barHeight);

    svgForLegendStuff.selectAll(".leftLegend")
            .data(data)
            .enter().append("g")
            .attr("class", "leftLegend").append("text")
            .attr("text-anchor", "middle")
            .attr("x", leftLegendPositionX)
            .attr("y", leftLegendPositionY).attr("font-size", fontSize)
            .attr("dy", 0)
            .text(function (d, i) {
                if (i === 0) {
                    return d.value.toFixed(2);
                }
                return " ";
            });

    svgForLegendStuff.selectAll(".rightLegend")
            .data(data)
            .enter().append("g")
            .attr("class", "rightLegend").append("text")
            .attr("text-anchor", "left")
            .attr("x", rightLegendPositionX)
            .attr("y", rightLegendPositionY)
            .attr("font-size", fontSize)
            .attr("dy", 0)
            .text(function (d, i) {
                if (i === (data.length - 1)) {
                    return d.value.toFixed(2);
                }
                return " ";
            });

    for (var i = 0; i < numberHues; i++) {
        theHue = hueStart + deltaHue * i;
        rgbString = color;
        opacity = opacityStart + deltaOpacity * i;
        p = 0 + deltaPercent * i;
        theData.push({"rgb": rgbString, "opacity": opacity, "percent": p});
    }

    var stops = d3.select('#' + idGradient).selectAll('stop')
            .data(theData);
    stops.enter().append('stop');
    stops.attr('offset', function (d) {
        return d.percent;
    })
            .attr('stop-color', function (d) {
                return d.rgb;
            })
            .attr('stop-opacity', function (d) {
                return d.opacity;
            });
}
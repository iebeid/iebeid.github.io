/* 
 * Author : Islam Akef Ebeid
 * Affiliations : University of Arkansas at Little Rock - Emerging Analytics Center
 * xlpm.js displays heavily curated tandem MS/MS peptide & residue cross-linking data
 */

// Global Variables
unit = 25;
scaleValue = 1;
fileWeight = 0;
treemapX = 0;
treemapY = 0;
treemapWidth = 0;
treemapHight = 0;
colorLegendHeight = 0;
thirdLevelWidth = 0;
thirdLevelHeight = 0;
thirdLevelX = 0;
thirdLevelY = 0;
visGroup = 0;
calculatedHeight = 0;
calculatedWidth = 0;
layoutObj = null;
sequences_table_taffy = [];
character_table_taffy = [];
peptide_1_selected = [];
peptide_2_selected = [];

function init(svgDim) {
    var width = Math.max(svgDim.w, 860);
    var height = Math.max(svgDim.h, 760);
    $("#vis").empty().width(width).height(height);
    layoutObj = new Layout("vis");
    layoutObj.constructViewPortMatrix();
    var svg = layoutObj.getSvg();
    svg.style("font-family", "Helvetica, Arial, sans-serif").style("font-size", "8px");
    var infoGroup = svg.append("g").attr("id", "infoGroup");
    layoutObj.putObjectAt(2, 2, infoGroup);
    var legendGroup = infoGroup.append("g").attr("id", "legendGroup");
    var scaleGroup = infoGroup.append("g").attr("id", "scaleGroup");
    visGroup = svg.append("g").attr("id", "visGroup");
    layoutObj.putObjectAt(2, 10, visGroup);
    var firstGroup = visGroup.append("g").attr("id", "first");
    var secondGroup = visGroup.append("g").attr("id", "second");
    var thirdGroup = visGroup.append("g").attr("id", "third");
    return {width: width, height: height};
}

// Utility functions
function clearSecondLevelData() {
    d3.select("#third").remove();
    d3.select("#second").remove();
    d3.select("#first").attr("transform", "scale(1)");
    constructStructuresPDB();
    $("#drilldown-status").html("<strong>Level 1 Active (Global Peptide Matrix):</strong> Cleared Level 2 &amp; Level 3 drill-downs. Click any <span style='color:#1d4ed8;font-weight:700;'>blue cross-linked cell</span> to inspect MS/MS precursor scans.");
}

function clearSVG() {
    loadPresetDataset(currentPresetId || "rim1_dimer");
}

function minimize(group, x, y, value) {
    var s = Snap(group);
    if (!s) return;
    var g = s;
    var myMatrix = new Snap.Matrix();
    myMatrix.scale(value, value);
    myMatrix.translate(x, y);
    myMatrix.invert();
    g.animate({transform: myMatrix}, 1200, mina.bounce, function () {
        g.animate({transform: myMatrix}, 1200, mina.bounce);
    });
}

function maximize(group, x, y, value) {
    var s = Snap(group);
    if (!s) return;
    var g = s;
    var myMatrix = new Snap.Matrix();
    myMatrix.scale(value, value);
    myMatrix.translate(x, y);
    myMatrix.invert();
    g.animate({transform: myMatrix}, 1200, mina.bounce, function () {
        g.animate({transform: myMatrix}, 1200, mina.bounce);
    });
}

// Create main SVG element dimensions
function calculateLWSVG(fastaFile) {
    var countValid = 0;
    var firstSeq = "";
    var secondSeq = "";
    var lines = fastaFile.split('\n');
    for (var j = 0; j < lines.length; j++) {
        var line = lines[j].trim();
        if (line.length !== 0) {
            if (line[0] === '>') {
                countValid++;
                continue;
            }
            if (countValid === 1) {
                firstSeq += line;
            }
            if (countValid > 1) {
                secondSeq += line;
            }
        }
    }
    calculatedHeight = Math.max(secondSeq.length * 8, 760);
    var containerWidth = document.getElementById("vis-wrapper") ? document.getElementById("vis-wrapper").clientWidth : document.getElementById("vis").clientWidth;
    calculatedWidth = Math.max((containerWidth || 1050) - 25, 900);
    unit = (calculatedWidth / calculatedHeight) * 1.68 + 20;
    fileWeight = firstSeq.length * secondSeq.length;
    return {w: calculatedWidth, h: calculatedHeight};
}

// Parse data from the 2 input files (FASTA, spectra data)
function checkForSpecialCharacters(sequence) {
    var specialChars = ["!", "@", "#", "$", "%", "^"];
    var specialCharactersObjectsArray = [
        {char: "!", rep: "C"},
        {char: "@", rep: "C"},
        {char: "#", rep: "C"},
        {char: "$", rep: "M"},
        {char: "%", rep: "N"},
        {char: "^", rep: "Q"}
    ];
    var input = sequence.toString();
    var specialCharactersObjectsArrayTaffy = TAFFY(specialCharactersObjectsArray);
    var indecies = [];
    function setCharAt(str, index, chr) {
        var returnStr;
        for (var i = 0; i < str.length; i++) {
            var firsPart = str.substring(0, index);
            var secondPart = str.substring(index + 1, str.length);
            returnStr = firsPart + chr + secondPart;
        }
        return returnStr;
    }
    for (var i = 0; i < input.length; i++) {
        if (specialChars.indexOf(input[i]) !== -1) {
            indecies.push(i);
        }
    }
    var pears = input;
    for (var j = 0; j < indecies.length; j++) {
        var obj = specialCharactersObjectsArrayTaffy({char: input.charAt(indecies[j])}).get();
        pears = setCharAt(pears, indecies[j], obj[0].rep);
    }
    return pears;
}

function createSequenceTable(fastaFile) {
    var sequence_table = [];
    var countValid = 0;
    var counterRelay = 0;
    var firstSeq = "";
    var secondSeq = "";
    var lines = fastaFile.split('\n');
    for (var j = 0; j < lines.length; j++) {
        var line = lines[j].trim();
        if (line.length !== 0) {
            if (line[0] === '>') {
                countValid++;
                continue;
            }
            if (countValid === 1) {
                firstSeq += line;
            }
            if (countValid > 1) {
                secondSeq += line;
            }
        }
    }
    if (firstSeq[firstSeq.length - 1] !== "K") {
        firstSeq = firstSeq + "#K";
    }
    if (secondSeq[secondSeq.length - 1] !== "K") {
        secondSeq = secondSeq + "#K";
    }
    var splitseq1 = firstSeq.match(/([^KR])*[KR]?/g);
    splitseq1.pop();
    var resOffset1 = 1;
    for (var i = 0; i < splitseq1.length; i++) {
        if (i === splitseq1.length - 1) {
            var lastElement = splitseq1[i];
            if (lastElement[lastElement.length - 2] === "#") {
                splitseq1[i] = splitseq1[i].substring(0, lastElement.length - 2);
            }
        }
        var len1 = splitseq1[i].length;
        sequence_table.push({
            id: counterRelay,
            uniqueNumber: i,
            sequence: splitseq1[i].toString().toUpperCase(),
            countNumber: len1,
            startResi: resOffset1,
            type: 1
        });
        resOffset1 += len1;
        counterRelay++;
    }
    var splitseq2 = secondSeq.match(/([^KR])*[KR]?/g);
    splitseq2.pop();
    var resOffset2 = 1;
    for (var k = 0; k < splitseq2.length; k++) {
        if (k === splitseq2.length - 1) {
            var lastElement2 = splitseq2[k];
            if (lastElement2[lastElement2.length - 2] === "#") {
                splitseq2[k] = splitseq2[k].substring(0, lastElement2.length - 2);
            }
        }
        var len2 = splitseq2[k].length;
        sequence_table.push({
            id: counterRelay,
            uniqueNumber: k,
            sequence: splitseq2[k].toString().toUpperCase(),
            countNumber: len2,
            startResi: resOffset2,
            type: 2
        });
        resOffset2 += len2;
        counterRelay++;
    }
    return sequence_table;
}

function createBlockTable(dataFile) {
    var blocks = [];
    var precursorinfo = [];
    var lines = dataFile.split(/\r?\n/);
    var reactionCounter = 0;
    for (var j = 2; j < lines.length; j++) {
        var line = lines[j];
        if (line.length > 0) {
            if (isNaN(line[0]) && line[0] !== '\t') {
                var splitseq = line.split("\t");
                if (splitseq.length < 8) continue;
                var frag1Filtered = checkForSpecialCharacters(splitseq[2].toString().toUpperCase());
                var frag2Filtered = checkForSpecialCharacters(splitseq[3].toString().toUpperCase());
                reactionCounter++;
                blocks.push({
                    id: reactionCounter,
                    title: splitseq[0],
                    mz: splitseq[1],
                    fragment1: frag1Filtered.toString(),
                    fragment2: frag2Filtered.toString(),
                    tmass: splitseq[4],
                    amass: splitseq[5],
                    charge: splitseq[6],
                    score: splitseq[7]
                });
            } else {
                var info = reactionCounter + line;
                var splitinfo = info.split("\t");
                precursorinfo.push({
                    blockId: splitinfo[0],
                    frag1: splitinfo[2],
                    frag2: splitinfo[3],
                    score: splitinfo[4]
                });
            }
        }
    }
    return {blocks: blocks, precursorinfo: precursorinfo};
}

function createPointsTable(sequences, blocks) {
    var points = [];
    var filteredPoints = [];
    var pointsID = 0;
    function getUniqueNumberForSequence(fragment, sequence, type) {
        var uniqueNumber = 0;
        var seqObject = sequences({sequence: sequence, type: type}).get();
        if (seqObject.length === 0) {
            return 0;
        }
        if (seqObject.length === 1) {
            uniqueNumber = seqObject[0].uniqueNumber;
        }
        if (seqObject.length > 1) {
            seqObject.forEach(function (seqObj) {
                var dividedFrag = fragment.toString().toUpperCase().match(/([^KR])*[KR]?/g);
                dividedFrag.pop();
                dividedFrag.forEach(function (seq, i) {
                    if (sequence === seq) {
                        var dividedFragObj = sequences({sequence: dividedFrag[0], type: type}).get();
                        if (dividedFragObj.length > 0) {
                            uniqueNumber = dividedFragObj[0].uniqueNumber + i;
                        }
                    }
                });
            });
        }
        return uniqueNumber;
    }
    var result = blocks().get();
    result.forEach(function (r) {
        var seqs1 = r.fragment1;
        var splitseq1 = seqs1.match(/([^KR])*[KR]?/g);
        splitseq1.pop();
        var seqs2 = r.fragment2;
        var splitseq2 = seqs2.match(/([^KR])*[KR]?/g);
        splitseq2.pop();
        splitseq1.forEach(function (s1) {
            splitseq2.forEach(function (s2) {
                var sourceNumber = getUniqueNumberForSequence(seqs1.toString().toUpperCase(), s1, 1);
                var targetNumber = getUniqueNumberForSequence(seqs2.toString().toUpperCase(), s2, 2);
                points.push({
                    id: pointsID,
                    blockId: r.id,
                    sequence1: s1,
                    sequence2: s2,
                    score: r.score,
                    sourceNumber: sourceNumber,
                    targetNumber: targetNumber,
                    title: r.title,
                    mz: r.mz,
                    tmass: r.tmass,
                    amass: r.amass,
                    charge: r.charge
                });
                pointsID++;
            });
        });
    });
    var points_table = TAFFY(points);
    var query2 = points_table().distinct("sequence1", "sequence2");
    query2.forEach(function (element) {
        var elements = points_table({sequence1: element[0], sequence2: element[1]}).get();
        var elements_table = TAFFY(elements);
        var maxScore = elements_table().max("score");
        var pointObj = points_table({sequence1: element[0], sequence2: element[1], score: maxScore}).get();
        var sourceNumber = pointObj[0].sourceNumber;
        var targetNumber = pointObj[0].targetNumber;
        filteredPoints.push({
            source: sourceNumber,
            target: targetNumber,
            value: parseFloat(maxScore),
            id: pointObj[0].id,
            sequence1: pointObj[0].sequence1,
            sequence2: pointObj[0].sequence2,
            title: pointObj[0].title,
            mz: pointObj[0].mz,
            tmass: pointObj[0].tmass,
            amass: pointObj[0].amass,
            charge: pointObj[0].charge
        });
    });
    var filteredPointsTable = TAFFY(filteredPoints);
    return {filteredPointsTable: filteredPointsTable, points_table: points_table};
}

function createSlider() {
    var height = unit;
    var width = document.getElementById("vis").offsetWidth - (7 * unit);
    var x = d3.scale.linear().domain([0.1, 1.5]).range([0, width]).clamp(true);
    var brush = d3.svg.brush().x(x).extent([0, 0]).on("brush", brushed);
    var svg = d3.select("#scaleGroup");
    svg.attr("transform", "translate(" + 2 * unit + "," + 1.5 * unit + ")");
    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height / 2 + ")")
        .call(d3.svg.axis().scale(x).orient("bottom").tickSize(1).tickPadding(10).tickValues([0.1, 1.5]));
    var slider = svg.append("g").attr("class", "slider").call(brush);
    slider.selectAll(".extent,.resize").remove();
    slider.select(".background").attr("height", height);
    var handle = slider.append("circle")
        .attr("class", "handle")
        .attr("transform", "translate(0," + height / 2 + ")")
        .attr("r", 6)
        .style("fill", "#0284c7")
        .style("stroke", "#fff")
        .style("stroke-width", "2px")
        .style("cursor", "ew-resize");
    slider.call(brush.event).transition().duration(500).call(brush.extent([100, 100])).call(brush.event);
    function brushed() {
        if (fileWeight >= 20000) {
            scaleValue = 0.55;
            if (fileWeight >= 300000) {
                scaleValue = 0.22;
            }
        }
        if (fileWeight < 20000) {
            scaleValue = 0.75;
            if (fileWeight < 10000) {
                scaleValue = 1;
            }
        }
        var value = scaleValue;
        if (d3.event && d3.event.sourceEvent) {
            value = x.invert(d3.mouse(this)[0]);
            brush.extent([value, value]);
        }
        handle.attr("cx", x(value));
        d3.select("#first").attr("transform", "scale(" + value + ")");
    }
}

// Create first-level visualization of the whole spectra data file
function displaySequenceTable(sequence_table, width, height) {
    var rowCount = 0;
    var columnCount = 0;
    var seqOneCount = 0;
    var rowHeaders = [];
    var columnHeaders = [];
    var yCount = 0;
    var xCount = 0;
    var lengthValue = -3;
    var lengthValueText = -3;
    var temp = [3];
    var tempText = [3];
    var cellHeigts = [];
    var computedLengthsArray = [];
    var widthValue = -3;
    var widthValueText = -3;
    var anotherTempText = [3];
    var anotherTemp = [3];
    var cellWidths = [];
    var computedLengthsArrayColumn = [];

    sequence_table.forEach(function (node) {
        if (node.type === 1) {
            columnCount = columnCount + node.sequence.length;
            columnHeaders[xCount] = node.sequence;
            seqOneCount++;
            xCount++;
        }
        if (node.type === 2) {
            rowCount = rowCount + node.sequence.length;
            rowHeaders[yCount] = node.sequence;
            yCount++;
        }
    });

    var rect = d3.select("#first").append("rect")
        .attr("class", "background")
        .attr("width", width)
        .attr("height", height)
        .attr("fill", "#A9A9A9");

    var row = d3.select("#first").selectAll(".row")
        .data(rowHeaders)
        .enter().append("g")
        .attr("class", "row");

    row.append("text")
        .attr("x", 0)
        .attr("y", 8.272)
        .attr("dy", ".32em")
        .attr("text-anchor", "start")
        .text(function (d) { return d; })
        .attr("transform", function (d, i) {
            computedLengthsArray[i] = this.getComputedTextLength();
            lengthValueText = lengthValueText + tempText[i];
            tempText[i + 1] = computedLengthsArray[i];
            var h = lengthValueText;
            return "translate(0," + h + ")rotate(90)";
        });

    var column = d3.select("#first").selectAll(".column")
        .data(columnHeaders)
        .enter().append("g")
        .attr("class", "column");

    column.append("text")
        .attr("x", 0)
        .attr("y", 12.4)
        .attr("dy", ".32em")
        .attr("text-anchor", "start")
        .text(function (d) { return d; })
        .attr("transform", function (d, i) {
            computedLengthsArrayColumn[i] = this.getComputedTextLength();
            widthValueText = widthValueText + anotherTempText[i];
            anotherTempText[i + 1] = computedLengthsArrayColumn[i];
            var w = widthValueText;
            return "translate(" + w + ",-20)";
        });

    var totalWidth = 0;
    computedLengthsArrayColumn.forEach(function (w) { totalWidth += w; });
    var newWidth = totalWidth;

    var totalHeight = 0;
    computedLengthsArray.forEach(function (l) { totalHeight += l; });
    var newHeight = totalHeight;

    row.append("line").attr("stroke", "#fff")
        .attr("x2", newWidth)
        .attr("transform", function (d, i) {
            lengthValue = lengthValue + temp[i];
            temp[i + 1] = computedLengthsArray[i];
            var h = lengthValue;
            cellHeigts.push(h);
            return "translate(0," + h + ")";
        });

    column.append("line").attr("stroke", "#fff")
        .attr("x1", -newHeight)
        .attr("transform", function (d, i) {
            widthValue = widthValue + anotherTemp[i];
            anotherTemp[i + 1] = computedLengthsArrayColumn[i];
            var w = widthValue;
            cellWidths.push(w);
            return "translate(" + w + ")rotate(-90)";
        });

    rect.attr("width", newWidth).attr("height", newHeight);
    var cellHeightLastElement = cellHeigts[cellHeigts.length - 1] + computedLengthsArray[computedLengthsArray.length - 1];
    var cellWidthsLastElement = cellWidths[cellWidths.length - 1] + computedLengthsArrayColumn[computedLengthsArrayColumn.length - 1];
    cellHeigts.push(cellHeightLastElement);
    cellWidths.push(cellWidthsLastElement);
    return {
        cellHeigts: cellHeigts,
        cellWidths: cellWidths,
        rectHeight: newHeight,
        rectWidth: newWidth
    };
}

function createDataPointsOnMatrix(cellHeigts, cellWidths, pointsTaffyObject, points_table, blocks, precursorinfo, color, newHeight, newWidth) {
    var matrix = [];
    var rowCellHeigtsTemp = [0];
    var rowCellHeigts = [0];
    var rowColumnWidthsTemp = [0];
    var rowColumnWidths = [0];

    for (var i = 0; i < cellHeigts.length; i++) {
        matrix[i] = d3.range(cellWidths.length).map(function () {
            return {
                w: 0, h: 0, positionX: 0, positionY: 0, title: '', mz: 0, tmass: 0,
                amass: 0, charge: 0, sequence1: '', sequence2: '', source: 0, target: 0, value: 0
            };
        });
    }

    var points = pointsTaffyObject().get();
    points.forEach(function (point) {
        if (matrix[point.target] && matrix[point.target][point.source]) {
            matrix[point.target][point.source].title = point.title;
            matrix[point.target][point.source].mz = point.mz;
            matrix[point.target][point.source].tmass = point.tmass;
            matrix[point.target][point.source].amass = point.amass;
            matrix[point.target][point.source].charge = point.charge;
            matrix[point.target][point.source].sequence1 = point.sequence1;
            matrix[point.target][point.source].sequence2 = point.sequence2;
            matrix[point.target][point.source].source = point.target;
            matrix[point.target][point.source].target = point.source;
            matrix[point.target][point.source].value = point.value;
        }
    });

    cellHeigts.forEach(function (height, idx) {
        var temp = rowCellHeigtsTemp[idx] - height;
        idx += 1;
        rowCellHeigtsTemp[idx] = height;
        rowCellHeigts[idx] = Math.abs(temp);
    });
    cellWidths.forEach(function (width, idx) {
        var temp = rowColumnWidthsTemp[idx] - width;
        idx += 1;
        rowColumnWidthsTemp[idx] = width;
        rowColumnWidths[idx] = Math.abs(temp);
    });

    rowCellHeigts.shift();
    rowCellHeigts.shift();
    rowColumnWidths.shift();
    rowColumnWidths.shift();
    rowCellHeigtsTemp.shift();
    rowColumnWidthsTemp.shift();

    var existingData = [];
    matrix.forEach(function (d, rIdx) {
        d.forEach(function (cell, cIdx) {
            if (cell.value !== 0) {
                cell.w = rowColumnWidths[cIdx];
                cell.h = rowCellHeigts[rIdx];
                cell.positionX = rowColumnWidthsTemp[cIdx];
                cell.positionY = rowCellHeigtsTemp[rIdx];
                existingData.push(cell);
            }
        });
    });

    var fillOpacities = [];
    var colorSelected = {color: '', opacity: 0};
    var blockArraySorted = existingData.slice().sort(function (a, b) {
        return a.value - b.value;
    });
    var minScore = blockArraySorted.length > 0 ? blockArraySorted[0].value : 0;
    var maxScore = blockArraySorted.length > 0 ? blockArraySorted[blockArraySorted.length - 1].value : 1;
    var z = d3.scale.linear().domain([minScore, maxScore]).range([0.22, 1]);
    var fillOpacitiesTaffy;

    existingData.forEach(function (d) {
        d3.select("#first").append("rect")
            .attr("x", d.positionX)
            .attr("y", d.positionY)
            .attr("width", Math.max(d.w - 1, 2))
            .attr("height", Math.max(d.h - 1, 2))
            .style("fill", color)
            .style("cursor", "pointer")
            .style("fill-opacity", function () {
                var opacityValue = z(d.value);
                colorSelected.opacity = opacityValue;
                fillOpacities.push({opacityValue: opacityValue, value: d.value});
                fillOpacitiesTaffy = TAFFY(fillOpacities);
                return opacityValue;
            })
            .on("click", function () {
                if (d3.event && d3.event.defaultPrevented) return;
                colorSelected.color = color;
                var opacityObject = fillOpacitiesTaffy({value: d.value}).get();
                colorSelected.opacity = opacityObject.length > 0 ? opacityObject[0].opacityValue : 0.8;
                d3.select("#third").remove();
                d3.select("#second").remove();
                visGroup.append("g").attr("id", "second");
                minimize("#first", 0, 0, scaleValue);
                $("#drilldown-status").html("<strong>Level 2 Active (MS/MS Spectral Treemap):</strong> Showing precursor scans for peptide pair <code>" + d.sequence1 + "</code> &times; <code>" + d.sequence2 + "</code> (Max Score: " + d.value.toFixed(4) + "). Click any treemap block on the right to open Level 3 &amp; highlight the 3D crystal structure.");
                createTreemap(points_table, d.sequence1, d.sequence2, blocks, precursorinfo, colorSelected);
            })
            .append("title")
            .text("Sequence 1: " + d.sequence1 + "\nSequence 2: " + d.sequence2 + "\nMax XLPM Score: " + d.value);
    });

    fillOpacities.sort(function (a, b) {
        return a.value - b.value;
    });
    var flags = [], fillOpacitiesDistinctArray = [];
    for (var m = 0; m < fillOpacities.length; m++) {
        if (flags[fillOpacities[m].value]) continue;
        flags[fillOpacities[m].value] = true;
        fillOpacitiesDistinctArray.push(fillOpacities[m]);
    }
    if (fillOpacitiesDistinctArray.length > 1) {
        makeLegend(fillOpacitiesDistinctArray, "#000099", 2 * unit, unit / 1.5, document.getElementById("vis").offsetWidth - (7 * unit), unit, "horizontal", "legendGroup", unit, "13px");
    }
    treemapX = (2 * unit) + (document.getElementById("vis").offsetWidth - (7 * unit));
    colorLegendHeight = unit;
    return existingData;
}

// Create the second level (Occurrences of every combination of sequences in MS/MS scans)
function createTreemap(points, sequence1, sequence2, blocks, precursorinfo, colorSelected) {
    var results = points({sequence1: sequence1, sequence2: sequence2}).get();
    var root = {name: sequence1 + " " + sequence2, children: []};
    results.forEach(function (result) {
        root.children.push({
            name: "possibility",
            blockId: result.blockId,
            size: parseFloat(result.score) || 0.1,
            amass: result.amass,
            charge: result.charge,
            mz: result.mz,
            sequence1: result.sequence1,
            sequence2: result.sequence2,
            title: result.title,
            tmass: result.tmass
        });
    });

    var width = 26 * unit;
    var height = 16 * unit;
    var x = d3.scale.linear().domain([0.01, 1.35]).range([10, 100]).clamp(true);
    var treemap = d3.layout.treemap()
        .size([width, height])
        .round(true)
        .sticky(true)
        .sort(function (a, b) { return a.size - b.size; })
        .value(function (d) { return x(d.size); });

    treemapWidth = width;
    treemapHeigt = height;
    treemapY = height + colorLegendHeight + unit;
    var transformYValue = 0;
    var transformXValue = Math.max(treemapX - width, 320);

    var treeMapGroup = d3.select("#second")
        .attr("transform", "translate(" + transformXValue + "," + transformYValue + ")");

    treeMapGroup.append("g").append("text")
        .text(function () { return "Level 2 Treemap: " + sequence1 + " × " + sequence2; })
        .attr("transform", "translate(0,-10)")
        .attr("font-size", "14px")
        .attr("font-weight", "bold")
        .attr("fill", "#0f172a");

    var cell = treeMapGroup.datum(root).selectAll(".leaf")
        .data(treemap.nodes(root))
        .enter().append("g")
        .attr("class", "leaf")
        .style("cursor", "pointer")
        .attr("transform", function (d) {
            return "translate(" + d.x + "," + d.y + ")";
        });

    cell.append("rect")
        .attr("width", function (d) { return Math.max(d.dx, 0); })
        .attr("height", function (d) { return Math.max(d.dy, 0); })
        .style("fill", function () { return colorSelected.color; })
        .style("fill-opacity", function () { return Math.max(colorSelected.opacity, 0.55); })
        .style("stroke", "#FFF")
        .style("stroke-width", "2");

    cell.append("foreignObject")
        .attr("x", 4).attr("y", 4)
        .attr("width", function (d) { return Math.max(d.dx - 8, 0); })
        .attr("height", function (d) { return Math.max(d.dy - 8, 0); })
        .append("xhtml:body")
        .style("margin", "0")
        .style("background", "transparent")
        .style("color", "#fff")
        .style("font-size", "9px")
        .style("font-family", "monospace")
        .style("overflow", "hidden")
        .html(function (d) {
            var blockData = blocks({id: d.blockId}).get();
            if (blockData.length !== 0) {
                return "<div><strong>" + blockData[0].fragment1 + "</strong></div>" +
                       "<div>" + blockData[0].fragment2 + "</div>" +
                       "<div>Score: " + parseFloat(blockData[0].score).toFixed(3) + "</div>";
            }
            return "";
        });

    cell.append("title")
        .text(function (d) {
            return "Scan Title: " + d.title + "\nm/z: " + d.mz + "\nCharge: " + d.charge + "\nTheoretical Mass: " + d.tmass + "\nActual Mass: " + d.amass;
        });

    cell.on("click", function (d) {
        if (!d.blockId) return;
        d3.select("#third").remove();
        visGroup.append("g").attr("id", "third");

        var blockData = blocks({id: d.blockId}).get();
        var splitseq1 = [];
        var splitseq2 = [];
        var peptideArray1 = [];
        var peptideArray2 = [];

        if (blockData.length !== 0) {
            splitseq1 = blockData[0].fragment1.match(/([^KR])*[KR]?/g);
            splitseq1.pop();
            splitseq2 = blockData[0].fragment2.match(/([^KR])*[KR]?/g);
            splitseq2.pop();
        }

        for (var i = 0; i < splitseq1.length; i++) {
            var s1 = splitseq1[i].toString().toUpperCase();
            var seqRes1 = sequences_table_taffy({sequence: s1, type: 1}).get();
            if (seqRes1.length > 0) {
                var start1 = seqRes1[0].startResi || (seqRes1[0].id + 1);
                for (var j = 0; j < seqRes1[0].countNumber; j++) {
                    peptideArray1.push(start1 + j);
                }
            }
        }

        for (var k = 0; k < splitseq2.length; k++) {
            var s2 = splitseq2[k].toString().toUpperCase();
            var seqRes2 = sequences_table_taffy({sequence: s2, type: 2}).get();
            if (seqRes2.length > 0) {
                var start2 = seqRes2[0].startResi || (seqRes2[0].id + 1);
                for (var m = 0; m < seqRes2[0].countNumber; m++) {
                    peptideArray2.push(start2 + m);
                }
            }
        }

        peptide_1_selected = peptideArray1.slice();
        peptide_2_selected = peptideArray2.slice();

        createFinalLevel(blocks, d.blockId, precursorinfo);

        var previousArray1 = [0];
        var previousArray2 = [0];
        view($("#firstseq").val(), $("#secondseq").val(), peptideArray1, peptideArray2, previousArray1, previousArray2, "0xA9A9A9", "0xA9A9A9", "0x0000ff");

        $("#drilldown-status").html("<strong>Level 3 Active (Residue Cross-Link Matrix + 3D Structure):</strong> Interacting peptides highlighted in <span style='color:#2563eb;font-weight:700;'>Blue</span> on the 3D crystal structure above. Click any <span style='color:#9a3412;font-weight:700;'>brown residue cell</span> in the Level 3 matrix to highlight the exact cross-linked amino acids in <span style='color:#dc2626;font-weight:700;'>Red</span>.");
    });
}

// Display Final Level (Precursor amino-acid site level)
function createFinalLevel(blocks, blockid, precursorinfo) {
    var blockdata = blocks({id: blockid}).get();
    var precursorinfodata = precursorinfo({blockId: blockid + ""}).get();
    var counterRelay = 0;
    var character_table = [];
    var frag1 = blockdata[0].fragment1;
    var frag2 = blockdata[0].fragment2;
    var splitseq1 = frag1.match(/./g);
    for (var i = 0; i < splitseq1.length; i++) {
        character_table.push({id: counterRelay, uniqueNumber: i, sequence: splitseq1[i].toString().toUpperCase(), type: 1});
        counterRelay++;
    }
    var splitseq2 = frag2.match(/./g);
    for (var j = 0; j < splitseq2.length; j++) {
        character_table.push({id: counterRelay, uniqueNumber: j, sequence: splitseq2[j].toString().toUpperCase(), type: 2});
        counterRelay++;
    }
    var transformYValue = treemapY + (1.2 * unit);
    var resultArray = displayCharacterTable(character_table);
    var transformXValue = Math.max(treemapX - treemapWidth - (thirdLevelWidth * 1.8) - 20, 260);
    thirdLevelX = transformXValue;
    thirdLevelY = transformYValue;
    d3.select("#third").attr("transform", "translate(" + transformXValue + ", 10)scale(1.65)");

    var filteredPoints = [];
    precursorinfodata.forEach(function (info) {
        var sourceNumber = parseInt(info.frag1, 10) - 1;
        var targetNumber = parseInt(info.frag2, 10) - 1;
        if (!isNaN(sourceNumber) && !isNaN(targetNumber) && sourceNumber >= 0 && targetNumber >= 0) {
            filteredPoints.push({source: sourceNumber, target: targetNumber, value: parseFloat(info.score)});
        }
    });
    var charTableObj = TAFFY(character_table);
    character_table_taffy = charTableObj;
    var filteredPointsTaffyObject = TAFFY(filteredPoints);
    createDataPointsOnMatrixForCharacterTable(resultArray.cellHeigts, resultArray.cellWidths, filteredPointsTaffyObject, charTableObj);
}

function displayCharacterTable(character_table) {
    var rowHeaders = [];
    var columnHeaders = [];
    var yCount = 0;
    var xCount = 0;
    var lengthValue = -3;
    var lengthValueText = -3;
    var temp = [3];
    var tempText = [3];
    var cellHeigts = [];
    var computedLengthsArray = [];
    var widthValue = -3;
    var widthValueText = -3;
    var anotherTempText = [3];
    var anotherTemp = [3];
    var cellWidths = [];
    var computedLengthsArrayColumn = [];

    character_table.forEach(function (node) {
        if (node.type === 1) {
            columnHeaders[xCount] = node.sequence;
            xCount++;
        }
        if (node.type === 2) {
            rowHeaders[yCount] = node.sequence;
            yCount++;
        }
    });

    var rect = d3.select("#third").append("rect")
        .attr("class", "backgroundThrd")
        .attr("width", 100)
        .attr("height", 100)
        .attr("fill", "#A9A9A9");

    var row = d3.select("#third").selectAll(".row")
        .data(rowHeaders)
        .enter().append("g")
        .attr("class", "row");

    var rowText = row.append("text")
        .attr("x", function (d) { return d === "I" ? 2.5 : 0; })
        .attr("y", 8)
        .attr("dy", ".32em")
        .attr("text-anchor", "start")
        .text(function (d) { return d; })
        .attr("overflow", function (d, i) {
            computedLengthsArray[i] = Math.max(this.getComputedTextLength(), 7);
        });

    var column = d3.select("#third").selectAll(".column")
        .data(columnHeaders)
        .enter().append("g")
        .attr("class", "column");

    var columnText = column.append("text")
        .attr("x", function (d) { return d === "I" ? 2.5 : 0; })
        .attr("y", 12)
        .attr("dy", ".32em")
        .attr("text-anchor", "start")
        .text(function (d) { return d; })
        .attr("overflow", function (d, i) {
            computedLengthsArrayColumn[i] = Math.max(this.getComputedTextLength(), 7);
        });

    computedLengthsArray.sort();
    computedLengthsArrayColumn.sort();

    rowText.attr("transform", function (d, i) {
        lengthValueText = lengthValueText + tempText[i];
        tempText[i + 1] = computedLengthsArray[computedLengthsArray.length - 1];
        var h = lengthValueText;
        return "translate(0," + h + ")rotate(90)";
    });

    columnText.attr("transform", function (d, i) {
        widthValueText = widthValueText + anotherTempText[i];
        anotherTempText[i + 1] = computedLengthsArrayColumn[computedLengthsArrayColumn.length - 1];
        var w = widthValueText;
        return "translate(" + w + ",-20)";
    });

    var totalHeight = 0;
    computedLengthsArray.forEach(function () {
        totalHeight += computedLengthsArray[computedLengthsArray.length - 1];
    });
    var newHeight = totalHeight;

    var totalWidth = 0;
    computedLengthsArrayColumn.forEach(function () {
        totalWidth += computedLengthsArrayColumn[computedLengthsArrayColumn.length - 1];
    });
    var newWidth = totalWidth;

    row.append("line").attr("stroke", "#fff")
        .attr("x2", newWidth)
        .attr("transform", function (d, i) {
            lengthValue = lengthValue + temp[i];
            temp[i + 1] = computedLengthsArray[computedLengthsArray.length - 1];
            var h = lengthValue;
            cellHeigts.push(h);
            return "translate(0," + h + ")";
        });

    column.append("line").attr("stroke", "#fff")
        .attr("x1", -newHeight)
        .attr("transform", function (d, i) {
            widthValue = widthValue + anotherTemp[i];
            anotherTemp[i + 1] = computedLengthsArrayColumn[computedLengthsArrayColumn.length - 1];
            var w = widthValue;
            cellWidths.push(w);
            return "translate(" + w + ")rotate(-90)";
        });

    rect.attr("width", newWidth).attr("height", newHeight);
    var lastH = cellHeigts[cellHeigts.length - 1] + computedLengthsArray[computedLengthsArray.length - 1];
    var lastW = cellWidths[cellWidths.length - 1] + computedLengthsArrayColumn[computedLengthsArrayColumn.length - 1];
    cellHeigts.push(lastH);
    cellWidths.push(lastW);
    thirdLevelWidth = newWidth;
    thirdLevelHeight = newHeight;
    return {
        cellHeigts: cellHeigts,
        cellWidths: cellWidths,
        rectHeight: newHeight,
        rectWidth: newWidth
    };
}

function createDataPointsOnMatrixForCharacterTable(cellHeigts, cellWidths, pointsTaffyObject, points_table) {
    var matrix = [];
    var rowCellHeigtsTemp = [0];
    var rowCellHeigts = [0];
    var rowColumnWidthsTemp = [0];
    var rowColumnWidths = [0];

    for (var i = 0; i < cellHeigts.length; i++) {
        matrix[i] = d3.range(cellWidths.length).map(function (j) {
            return {w: 0, h: 0, positionX: 0, positionY: 0, char1: '', char2: '', source: j, target: i, score: 0};
        });
    }

    var points = pointsTaffyObject().get();
    if (points.length !== 0) {
        points.forEach(function (point) {
            if (matrix[point.target] && matrix[point.target][point.source]) {
                var c1 = points_table({uniqueNumber: point.source, type: 1}).get();
                var c2 = points_table({uniqueNumber: point.target, type: 2}).get();
                matrix[point.target][point.source].score = point.value;
                matrix[point.target][point.source].char1 = c1.length > 0 ? c1[0].sequence : '';
                matrix[point.target][point.source].char2 = c2.length > 0 ? c2[0].sequence : '';
            }
        });
    }

    cellHeigts.forEach(function (height, idx) {
        var temp = rowCellHeigtsTemp[idx] - height;
        idx += 1;
        rowCellHeigtsTemp[idx] = height;
        rowCellHeigts[idx] = Math.abs(temp);
    });
    cellWidths.forEach(function (width, idx) {
        var temp = rowColumnWidthsTemp[idx] - width;
        idx += 1;
        rowColumnWidthsTemp[idx] = width;
        rowColumnWidths[idx] = Math.abs(temp);
    });

    rowCellHeigts.shift();
    rowCellHeigts.shift();
    rowColumnWidths.shift();
    rowColumnWidths.shift();
    rowCellHeigtsTemp.shift();
    rowColumnWidthsTemp.shift();

    var existingData = [];
    matrix.forEach(function (d, rIdx) {
        d.forEach(function (cell, cIdx) {
            if (cell.score !== 0 && rowColumnWidths[cIdx] && rowCellHeigts[rIdx]) {
                cell.w = rowColumnWidths[cIdx];
                cell.h = rowCellHeigts[rIdx];
                cell.positionX = rowColumnWidthsTemp[cIdx];
                cell.positionY = rowCellHeigtsTemp[rIdx];
                existingData.push(cell);
            }
        });
    });

    var fillOpacities = [];
    var minScore = 0;
    var maxScore = 1;
    if (existingData.length > 1) {
        var blockArraySorted = existingData.slice().sort(function (a, b) {
            return a.score - b.score;
        });
        minScore = blockArraySorted[0].score;
        maxScore = blockArraySorted[blockArraySorted.length - 1].score;
    } else if (existingData.length === 1) {
        minScore = 0;
        maxScore = existingData[0].score;
    }

    var z = d3.scale.linear().domain([minScore, maxScore]).range([0.45, 1]).clamp(true);
    var savedPeptide1 = peptide_1_selected.slice();
    var savedPeptide2 = peptide_2_selected.slice();

    existingData.forEach(function (d) {
        d3.select("#third").append("rect")
            .attr("x", d.positionX)
            .attr("y", d.positionY)
            .attr("width", Math.max(d.w - 1, 2))
            .attr("height", Math.max(d.h - 1, 2))
            .style("fill", "brown")
            .style("cursor", "pointer")
            .style("fill-opacity", function () {
                var opacityValue = z(d.score);
                fillOpacities.push({opacityValue: opacityValue, value: d.score});
                return opacityValue;
            })
            .on("click", function () {
                var resi1 = savedPeptide1[d.source] || savedPeptide1[0] || 1;
                var resi2 = savedPeptide2[d.target] || savedPeptide2[0] || 1;
                var peptideArray1 = [resi1];
                var peptideArray2 = [resi2];
                view($("#firstseq").val(), $("#secondseq").val(), peptideArray1, peptideArray2, savedPeptide1, savedPeptide2, "0xA9A9A9", "0x0000ff", "0xff0000");
                $("#drilldown-status").html("<strong>Residue Cross-Link Pinpointed on 3D Structure:</strong> Residue <code>" + d.char1 + " (pos " + resi1 + ")</code> &times; Residue <code>" + d.char2 + " (pos " + resi2 + ")</code> highlighted in <span style='color:#dc2626;font-weight:700;'>Red</span> within the <span style='color:#2563eb;font-weight:700;'>Blue</span> peptide chains (Site Score: " + d.score.toFixed(4) + ").");
            })
            .append("title")
            .text("Residue 1: " + d.char1 + "\nResidue 2: " + d.char2 + "\nSite Score: " + d.score);
    });

    fillOpacities.sort(function (a, b) {
        return a.value - b.value;
    });
    if (fillOpacities.length > 1) {
        makeLegend(fillOpacities, "brown", 0, thirdLevelHeight + 5, Math.max(thirdLevelWidth - 15, 40), 8, "horizontal", "third", unit, "5px");
    }
    return existingData;
}

function main(fastaFile, dataFile) {
    if (!fastaFile || !dataFile) return;
    $("#vis").show();
    $("#structure").show();
    if (localFlag === true) {
        constructStructuresPDB();
    } else {
        constructStructures();
    }
    var dim = calculateLWSVG(fastaFile);
    var sequence_table = createSequenceTable(fastaFile);
    var sequences = TAFFY(sequence_table);
    sequences_table_taffy = sequences;
    var block_table = createBlockTable(dataFile);
    var blocks = TAFFY(block_table.blocks);
    var precursorinfo = TAFFY(block_table.precursorinfo);
    var initObj = init(dim);
    var resultArray = displaySequenceTable(sequence_table, initObj.width, initObj.height);
    var points = createPointsTable(sequences, blocks);
    createDataPointsOnMatrix(resultArray.cellHeigts, resultArray.cellWidths, points.filteredPointsTable, points.points_table, blocks, precursorinfo, "#000099", resultArray.rectHeight, resultArray.rectWidth);
    createSlider();
}

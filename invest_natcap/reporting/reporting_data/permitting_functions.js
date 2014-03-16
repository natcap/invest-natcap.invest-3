$(document).ready(function(){
    //Get a handle on the two JSON data objects set in the html json tags
    var globalMuniData = JSON.parse(document.getElementById('muni-data').innerHTML);
    var globalImpactData = JSON.parse(document.getElementById('impact-data').innerHTML);

    //Check to see if any formatting options have been indicated
    check_number_format();

    //State of current selected parcel_ids
    var jsonState = {};
    //State of current municipalities
    var muniState = {};
    //Handle on the 'last' table, municipality table
    $tableLast = $('table:last');

    //Object that maps municipality column indices to municipality names
    var muniColMap = {};
    //Array of municipality table column indices
    var muniColIndexList = [];
    //Build up muniColMap and muniColIndexList
    $tableLast.find("th").each(function(){
        muniColMap[$(this).index()] = $(this).html();
        muniColIndexList.push($(this).index());
    });
    //Sort the indices
    muniColIndexList.sort();
    //console.log('muniColIndexList');
    //console.log(muniColIndexList);
    //Array to hold municipality column names in order
    var muniColList = [];
    //Build up muniColList
    for(var colIndex in muniColIndexList){
        muniColList.push(muniColMap[colIndex]);
    }
    console.log('muniColList');
    console.log(muniColList);

    initiate_impacts(muniState, muniColList, globalImpactData);
    console.log('returned munistate');
    console.log(muniState);

    var offsetsList = [];
    $tableLast.find('th.offsets').each(function(){
        offsetsList.push($(this).html());
    });
    var netList = [];
    $tableLast.find('th.net').each(function(){
        netList.push($(this).html());
    });

    //Impact muni list from json object
    muniImpactList = [];
    for(var key in globalImpactData){
       muniImpactList.push(key);
    }

    //On a checkbox change event
    $('[name="cb"]').change(function() {

        $table = $(this).closest('table');

        //Get handle on the parcel_id column index
        var par_index = $table.find('th:contains("parcel_id")').index();
        //Get the parcel_id related to the changed checkbox
        var par_id = $(this).closest('tr').find('td:eq(' + par_index + ')').html();

        //ADD and update
        if(this.checked){
            //Add parcel_id to jsonState with data
            jsonState[par_id] = globalMuniData[par_id];
            //Get the munis from parcel_id data
            var munis = jsonState[par_id]['municipalities'];
            for(muni in munis){
                //Get the percentage as decimal to multiply values with
                var perc = munis[muni];
                if(muni in muniState){
                    muniDict = muniState[muni];
                    //Handle updating the muni
                    //Update the count of parcel ids representing the
                    //municipality
                    if('count' in muniState[muni]){
                        muniDict['count'] = muniDict['count'] + 1;
                    }
                    else{
                        muniDict['count'] = 2;
                    }
                    //Get handle on the row of the municipality we want to
                    //update
                    $td = $tableLast.find('td:contains("' + muni + '")');
                    $tr = $td.closest('tr');

                    muniOffsets = muniDict['offsets'];
                    muniNets = muniDict['nets'];
                    $.each(offsetList, function(index, offset){
                        offsetBase = offset.substr(0, offset.indexOf('_'));
                        netColName = offsetBase + '_net';
                        var adjustedVal = jsonState[par_id][offsetBase] * perc;
                        muniOffsets[offset] = muniOffsets[offset] + adjustedVal;
                        muniNets[netColName] = muniNets[netColName] + adjustedVal;

                        offsetIndex = $tableLast.find('th:contains("' + offset + '")').index();
                        netIndex = $tableLast.find('th:contains("' + netColName + '")').index();
                        $tr.find('td:eq(' + offsetIndex + ')').html(muniOffsets[offset]);
                        $tr.find('td:eq(' + netIndex + ')').html(muniNets[netColName]);
                    });
                }
                else{
                    //Add new municipality
                    muniState[muni] = {};
                    //Add a counter to track if the municipality is still
                    //represented by the parcel ids
                    muniState[muni]['count'] = 1;

                    muniDict = muniState[muni];
                    muniDict['pop'] = globalImpactData[muni]['pop'];

                    muniDict['offsets'] = {};
                    muniDict['nets'] = {};
                    muniDict['impacts'] = {};

                    $.each(offsetList, function(index, offset){
                        offsetBase = offset.substr(0, offset.indexOf('_'));
                        netColName = offsetBase + '_net';
                        impactColName = offsetBase + '_impact';
                        muniDict['offsets'][offset] = jsonState[par_id][offsetBase] * perc;
                        muniDict['impacts'][impactColName] = 0.0;
                        muniDict['nets'][netColName] = jsonState[par_id][offsetBase] * perc;
                    });

                    var rowString = "<tr>";
                    $.each(muniColList, function(index, colName){

                        if(colName == 'municipalities'){
                            rowString = rowString + "<td>" + muni + "</td>";}
                        else if(colName == "pop"){
                            rowString = rowString + "<td>" + muniDict[colName] + "</td>";
                            }
                        else if(impactList.indexOf(colName) != -1){
                            rowString = rowString + "<td>" + muniDict['impacts'][colName] + "</td>";
                            }
                        else if(offsetList.indexOf(colName) != -1){
                            rowString = rowString + "<td>" + muniDict['offsets'][colName] + "</td>";
                            }
                        else if(netList.indexOf(colName) != -1){
                            rowString = rowString + "<td>" + muniDict['nets'][colName] + "</td>";
                            }
                        else {
                            console.log("ERROR handling column name for impact row : " + colName);
                            }
                    });

                    rowString = rowString + "</tr>";
                    $tableLast.append(rowString);
                }
            }
        }
        else{
            //Get the munis from parcel_id data
            var munis = jsonState[par_id]['municipalities'];
            for(muni in munis){
                //Get the percentage as decimal to multiply values with
                var perc = munis[muni];
                //Either a municipality needs to be updated or removed
                muniState[muni]['count'] = muniState[muni]['count'] - 1;
                if(muniState[muni]['count'] == 0){
                    //Delete row, delete muni
                    //Get handle on the row
                    $td = $tableLast.find('td:contains("' + muni + '")');
                    $tr = $td.closest('tr');
                    //Fade out effect, when removing row
                    $tr.fadeOut(200, function(){
                        $tr.remove();
                        });
                    //Delete muni from muniState object
                    delete muniState[muni];
                }
                else{
                    //Update row by subtracting values removed by unchecking a
                    //parcel id
                    //Get handle on the row
                    $td = $tableLast.find('td:contains("' + muni + '")');
                    $tr = $td.closest('tr');

                    var muniDict = muniState[muni];

                    muniOffsets = muniDict['offsets'];
                    muniNets = muniDict['nets'];
                    $.each(offsetList, function(index, offset){
                        offsetBase = offset.substr(0, offset.indexOf('_'));
                        netColName = offsetBase + '_net';
                        var adjustedVal = jsonState[par_id][offsetBase] * perc;
                        muniOffsets[offset] = muniOffsets[offset] - adjustedVal;
                        muniNets[netColName] = muniNets[netColName] - adjustedVal;

                        offsetIndex = $tableLast.find('th:contains("' + offset + '")').index();
                        netIndex = $tableLast.find('th:contains("' + netColName + '")').index();
                        $tr.find('td:eq(' + offsetIndex + ')').html(muniOffsets[offset]);
                        $tr.find('td:eq(' + netIndex + ')').html(muniNets[netColName]);
                    });

                }
            }
            //Update jsonState by deleting the parcel id that was unchecked
            delete jsonState[par_id];
            console.log(globalMuniData[par_id]);
        }
        check_number_format();
    });
});

function initiate_impacts(muniState, muniColList, globalImpactData) {

    function get_col_class(name){
        var classList = [];
        $tableLast.find('th.' + name).each(function(){
            classList.push($(this).html());
        });

        return classList;
    }

    offsetList = get_col_class('offsets');
    impactList = get_col_class('impacts');
    netList = get_col_class('net');

    console.log('offsetList');
    console.log(offsetList);

    for(var muniKey in globalImpactData){
        if('impacts' in globalImpactData[muniKey]){
            muniState[muniKey] = globalImpactData[muniKey];
            muniDict = muniState[muniKey];

            muniDict['offsets'] = {};
            muniDict['nets'] = {};
            $.each(offsetList, function(index, offset){
                muniDict['offsets'][offset] = 0.0;
                });
            $.each(netList, function(index, net){
                colBase = net.substr(0, net.indexOf('_'));
                impactEqu = colBase + '_impact';
                muniDict['nets'][net] = -1.0 * muniDict['impacts'][impactEqu];
                });
        }
    }

    console.log('muniSate');
    console.log(muniState);

    for(muniKey in muniState){
        muniDict = muniState[muniKey];
        var rowString = "<tr>";
        $.each(muniColList, function(index, colName){

            if(colName == 'municipalities'){
                rowString = rowString + "<td>" + muniKey + "</td>";}
            else if(colName == "pop"){
                rowString = rowString + "<td>" + muniDict[colName] + "</td>";
                }
            else if(impactList.indexOf(colName) != -1){
                rowString = rowString + "<td>" + muniDict['impacts'][colName] + "</td>";
                }
            else if(offsetList.indexOf(colName) != -1){
                rowString = rowString + "<td>" + muniDict['offsets'][colName] + "</td>";
                }
            else if(netList.indexOf(colName) != -1){
                rowString = rowString + "<td>" + muniDict['nets'][colName] + "</td>";
                }
            else {
                console.log("ERROR handling column name for impact row : " + colName);
            }
        });

        rowString = rowString + "</tr>";
        $tableLast.append(rowString);
    }
}

function check_number_format() {
    //This function checks to see if any columns should have
    //numbers formatted in scientific notation

    //Search for class names of scientific which indicate the column
    //should be represented in scientific notation
    $('.scientific').each(function(){
        //console.log($(this).index());
        //Get the index for the column the class name is found at.
        //Add 1 because 'nth-child' below starts indexing at 1
        var col_index = $(this).index() + 1;
        //Get the table associated with class scientific, find all
        //table data with the same index and iterate over
        $(this).closest('table').find("td:nth-child("+col_index+")").each(function(){
            //Get html value from table data
            var value = $(this).html();
            //console.log(value);
            //Make sure the value is a number to operate properly on
            if ($.isNumeric(value)){
                //Cast and set html value to exponential format
                $(this).html(parseFloat(value).toExponential());
            }
        });
    });
}

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
    var $tableLast = $('table:last');

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
    //console.log('muniColList');
    //console.log(muniColList);

    //If any municipalities have starting impacts add them to the table
    initiate_impacts(muniState, muniColList, globalImpactData);
    //console.log('returned munistate');
    //console.log(muniState);

    //Get arrays of the column headers by class names
    var offsetList = get_col_class('offsets');
    var impactList = get_col_class('impacts');
    var netList = get_col_class('net');

    //On a checkbox change event
    $('[name="cb"]').change(function() {

        //Get a handle on the table where the checkbox was made
        var $table = $(this).closest('table');

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
            for(var muni in munis){
                //Get the percentage as decimal to adjust values with
                var perc = munis[muni];
                //Update municipality if municipality is already tracked
                if(muni in muniState){
                    var muniDict = muniState[muni];
                    //Update the count of parcel ids representing the
                    //municipality
                    if('count' in muniState[muni]){
                        muniDict['count'] = muniDict['count'] + 1;
                    }
                    else{
                        //In here because a municipality was added in initial impacts
                        //Set to 2 so that we never remove the row, keeping the impacts
                        muniDict['count'] = 2;
                    }
                    //Get handle on the row of the municipality we want to
                    //update
                    var $td = $tableLast.find('td:contains("' + muni + '")');
                    var $tr = $td.closest('tr');
                    //Get the offsets object
                    var muniOffsets = muniDict['offsets'];
                    //Get the nets object
                    var muniNets = muniDict['nets'];
                    //For each offset column update offset and net columns
                    $.each(offsetList, function(index, offset){
                        //Get the name of the column before he underscore, used
                        //to correlate net and parcel columns
                        var offsetBase = offset.substr(0, offset.indexOf('_'));
                        //Net column name
                        var netColName = offsetBase + '_net';
                        //Get the adjusted offset value for the column from the
                        //parcel_id table
                        var adjustedVal = jsonState[par_id][offsetBase] * perc;
                        //Update the offsets / nets in the data structure
                        muniOffsets[offset] = muniOffsets[offset] + adjustedVal;
                        muniNets[netColName] = muniNets[netColName] + adjustedVal;
                        //Get index of corresponding offset and net column
                        var offsetIndex = $tableLast.find('th:contains("' + offset + '")').index();
                        var netIndex = $tableLast.find('th:contains("' + netColName + '")').index();
                        //Set new and update values in table for offset and net for column
                        $tr.find('td:eq(' + offsetIndex + ')').html(muniOffsets[offset]);
                        $tr.find('td:eq(' + netIndex + ')').html(muniNets[netColName]);
                    });
                }
                //Add new municipality to the tracking data structure
                //and to the municipality table
                else{
                    muniState[muni] = {};
                    //Add a counter to track if the municipality is still
                    //represented by the parcel ids
                    muniState[muni]['count'] = 1;

                    var muniDict = muniState[muni];
                    //Add population data to the data structure
                    muniDict['pop'] = globalImpactData[muni]['pop'];
                    //Create objects in the current object that track
                    //table information
                    muniDict['offsets'] = {};
                    muniDict['nets'] = {};
                    muniDict['impacts'] = {};
                    //For each column name in offsets add offset, impact
                    //and net value
                    $.each(offsetList, function(index, offset){
                        //Get the name of the column before the underscore, used
                        //to correlate net and parcel columns
                        var offsetBase = offset.substr(0, offset.indexOf('_'));
                        var netColName = offsetBase + '_net';
                        var impactColName = offsetBase + '_impact';
                        //Set offset value from parcel data adjusted to percentage
                        muniDict['offsets'][offset] = jsonState[par_id][offsetBase] * perc;
                        //Set impact values to 0 since, if we are adding a new municipality
                        //it was not originally set with having impacts
                        muniDict['impacts'][impactColName] = 0.0;
                        //Set nets to the same as offsets since there is no initial impacts
                        muniDict['nets'][netColName] = jsonState[par_id][offsetBase] * perc;
                    });
                    //Adding a new row so build up some html
                    var rowString = "<tr>";
                    //Iterate over the column names in the municipality table
                    //building html row string appropriately
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
                    //Add row to end of table
                    $tableLast.append(rowString);
                }
            }
        }
        //Parcel id is unchecked so update data / table
        else{
            //Get the munis from parcel_id data
            var munis = jsonState[par_id]['municipalities'];
            for(var muni in munis){
                //Get the percentage as decimal to multiply values with
                var perc = munis[muni];
                //Decrease the count by 1 since a parcel_id was unchecked
                muniState[muni]['count'] = muniState[muni]['count'] - 1;
                //If the muni is no longer represented by a parcel check
                //remove it
                if(muniState[muni]['count'] == 0){
                    //Get handle on the row
                    var $td = $tableLast.find('td:contains("' + muni + '")');
                    var $tr = $td.closest('tr');
                    //Fade out effect, when removing row
                    $tr.fadeOut(200, function(){
                        $tr.remove();
                        });
                    //Delete muni from muniState object
                    delete muniState[muni];
                }
                //Municipality is still represented either by a parcel check
                //or initial impact, so just update
                else{
                    //Get handle on the row
                    var $td = $tableLast.find('td:contains("' + muni + '")');
                    var $tr = $td.closest('tr');

                    //Get handle on data objects for updating
                    var muniDict = muniState[muni];
                    var muniOffsets = muniDict['offsets'];
                    var muniNets = muniDict['nets'];

                    $.each(offsetList, function(index, offset){
                        //Get the name of the column before the underscore, used
                        //to correlate net and parcel columns
                        var offsetBase = offset.substr(0, offset.indexOf('_'));
                        var netColName = offsetBase + '_net';
                        //Get the value that is being updated from parcel table
                        var adjustedVal = jsonState[par_id][offsetBase] * perc;
                        //Adjust the data structure with the update values of
                        //removing a checked parcel
                        muniOffsets[offset] = muniOffsets[offset] - adjustedVal;
                        muniNets[netColName] = muniNets[netColName] - adjustedVal;
                        //Get column index in table for offset and net column
                        var offsetIndex = $tableLast.find('th:contains("' + offset + '")').index();
                        var netIndex = $tableLast.find('th:contains("' + netColName + '")').index();
                        //Update the html in the table
                        $tr.find('td:eq(' + offsetIndex + ')').html(muniOffsets[offset]);
                        $tr.find('td:eq(' + netIndex + ')').html(muniNets[netColName]);
                    });

                }
            }
            //Update jsonState by deleting the parcel id that was unchecked
            delete jsonState[par_id];
            //console.log(globalMuniData[par_id]);
        }
        //Since we just updated some values, check to see if they
        //need to be formatted
        check_number_format();
    });
});

function get_col_class(name){
    //Helper function that returns an array of column names
    //that have a certain class name, 'name'
    var classList = [];
    //Handle on the 'last' table, municipality table
    var $tableLast = $('table:last');
    $tableLast.find('th.' + name).each(function(){
        classList.push($(this).html());
    });

    return classList;
}

function initiate_impacts(muniState, muniColList, globalImpactData) {
    //This function initiates any municipalities that have initial impacts
    //muniState - an object that tracks the state / data of municipalities
    //    currently in the table
    //muniColList - an Array of the municipality column names in order
    //globalImpactData - an object of the municipality JSON data

    //Handle on the 'last' table, municipality table
    var $tableLast = $('table:last');

    //Get arrays of the column headers by class names
    var offsetList = get_col_class('offsets');
    var impactList = get_col_class('impacts');
    var netList = get_col_class('net');

    //console.log('offsetList');
    //console.log(offsetList);

    for(var muniKey in globalImpactData){
        //Iterating over each municipality and constructing a working
        //object that represents the municipalities with initial impacts
        if('impacts' in globalImpactData[muniKey]){
            //Get population and impacts data
            muniState[muniKey] = globalImpactData[muniKey];
            var muniDict = muniState[muniKey];
            //Initialize inner objects for offsets and nets
            muniDict['offsets'] = {};
            muniDict['nets'] = {};
            //Initialize offset column data to 0
            $.each(offsetList, function(index, offset){
                muniDict['offsets'][offset] = 0.0;
                });
            //Initialize net values to the negative of the impact
            $.each(netList, function(index, net){
                var colBase = net.substr(0, net.indexOf('_'));
                var impactEqu = colBase + '_impact';
                muniDict['nets'][net] = -1.0 * muniDict['impacts'][impactEqu];
                });
        }
    }
    //console.log('muniSate');
    //console.log(muniState);

    for(var muniKey in muniState){
        //For each municipality that has an initial impact
        //build up a proper html row string to add to table

        var muniDict = muniState[muniKey];
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

var globalMuniData;
var globalImpactData;

$(document).ready(function()
        {
           //var jsonData = JSON.parse(document.getElementById('jsonData').innerHTML);
           //TODO: put below json parsing in function below, but outside of event handler
           globalMuniData = JSON.parse(document.getElementById('muni-data').innerHTML);
           globalImpactData = JSON.parse(document.getElementById('impact-data').innerHTML);

           console.log(globalMuniData);

           sum_constant_total();
           check_number_format();
        });

$(function(){
    //State of current selected parcel_ids
    var jsonState = {};
    //State of current municipalities
    var muniState = {};
    //The indexes for each above key found in muni table
    var muniIndicies = [];
    //Object that has the relationship between column index and column name
    var muniObj = {};
    //Handle on the 'last' table, municipality table
    $tableLast = $('table:last');
    //Interate over one instance of the JSON data to get the keys (municipality,
    //ecosystem services)
    for(var outKey in globalMuniData){
        for(inKey in globalMuniData[outKey]){
            var index = $tableLast.find('th:contains("'+inKey+'")').index();
            //Build up an object that points an index to its column string
            muniObj[index] = inKey;
            muniIndicies.push(index);
        }
        //We just want a handle on the inner String keys, so quit after one round
        break;
    }

    //Sort the indicies so the row string can be aggregated properly.
    muniIndicies.sort();

    //On a checkbox change event
    $('[name="cb"]').change(function() {

        $table = $(this).closest('table');

        //$('.checkTot').html("0");
        $table.find('.checkTot').html("0");
        //$('[name="cb"]:checked').closest('tr').find('.rowDataSd').each(function() {
        $table.find('[name="cb"]:checked').closest('tr').find('.rowDataSd').each(function() {
            var $td = $(this);
            //var $sumColumn = $(this).find('tr.checkTotal td:eq(' + $td.index() + ')');
            var $sumColumn = $table.find('tr.checkTotal td:eq(' + $td.index() + ')');
            var currVal = $sumColumn.html() || 0;
            currVal = +currVal + +$td.html();
            $sumColumn.html(currVal);
        });

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
                    //Handle updating the muni
                    //Update the count of parcel ids representing the
                    //municipality
                    muniState[muni]['count'] = muniState[muni]['count'] + 1;
                    //Get handle on the row of the municipality we want to
                    //update
                    $td = $tableLast.find('td:contains("' + muni + '")');
                    $tr = $td.closest('tr');
                    for(var colIndex in muniIndicies){
                        var colName = muniObj[colIndex];
                        if(colName != 'municipalities'){
                            var curVal = muniState[muni][colName];
                            var newVal = jsonState[par_id][colName] * perc;
                            $tdUp = $tr.find('td:eq(' + colIndex + ')');
                            console.log($tdUp.html());
                            //Making sure values are numbers with '+'
                            var upVal = +newVal + +curVal;
                            //Update muni state
                            muniState[muni][colName] = upVal;
                            //Add new value to table data spot
                            $tdUp.html(upVal);
                        }
                    }
                }
                else{
                    //Add new municipality
                    muniState[muni] = {};
                    //Add a counter to track if the municipality is still
                    //represented by the parcel ids
                    muniState[muni]['count'] = 1;
                    //Start a string for the new row to add
                    var newRow = '<tr>';
                    //Iterate over ordered column indices
                    for(var colIndex in muniIndicies){
                        //Get Corresponding column name
                        var colName = muniObj[colIndex];
                        //If its municipalities we just want to write the name
                        //to that data slot
                        if(colName=='municipalities'){
                            newRow = newRow + '<td>' + muni + '</td>';
                        }
                        else{
                            //Need to get the adjusted value based on percent
                            newRow = newRow + '<td>';
                            //Get adjusted value for column
                            var value = jsonState[par_id][colName] * perc;
                            //Update muniState
                            muniState[muni][colName] = value;
                            newRow = newRow + value + '</td>';
                        }
                    }
                    //Close new row
                    newRow = newRow + '</tr>';
                    //Add new row to table
                    $tableLast.append(newRow);
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
                    for(var colIndex in muniIndicies){
                        var colName = muniObj[colIndex];
                        if(colName != 'municipalities'){
                            var curVal = muniState[muni][colName];
                            var newVal = jsonState[par_id][colName] * perc;
                            $tdUp = $tr.find('td:eq(' + colIndex + ')');
                            console.log($tdUp.html());
                            var upVal = +curVal - +newVal;
                            muniState[muni][colName] = upVal;
                            $tdUp.html(upVal);
                        }
                    }
                }
            }
            //Update jsonState by deleting the parcel id that was unchecked
            delete jsonState[par_id];
            console.log(globalMuniData[par_id]);
        }

        check_number_format();
    });
});

function sum_constant_total() {

    $('table').each(function(){

        var totals_array = new Array();

        //var $dataRows=$("#my_table tr:not('.totalColumn')");
        var $dataRows=$(this).find("tr:not('.totalColumn')");

        $dataRows.each(function() {
            $(this).find('.rowDataSd').each(function(i){
                totals_array[i] = 0;
            });
        });

        $dataRows.each(function() {
            $(this).find('.rowDataSd').each(function(i){
                totals_array[i]+=parseFloat( $(this).html());
            });
        });

        //$("#my_table td.totalCol").each(function(i){
        $(this).find("td.totalCol").each(function(i){
            $(this).html(totals_array[i]);
        });
    });
}

function check_number_format() {
    //This function checks to see if any columns should have
    //numbers formatted in scientific notation
    $('.scientific').each(function(){
        console.log($(this).index());
        var col_index = $(this).index() + 1;
        $(this).closest('table').find("td:nth-child("+col_index+")").each(function(){
            var value = $(this).html();
            console.log(value);
            if ($.isNumeric(value)){
                $(this).html(parseFloat(value).toExponential());
            }
        });
    });
}
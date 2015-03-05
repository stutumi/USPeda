var heatmapData = []
var markers = []
var map
var heatmap
var infowindow
var pointArray
var pages 
var mappages 

var KEYCODE_ENTER = 13;
var KEYCODE_ESC = 27;

score_names = { 1: '1 - Péssimo', 
                2: '2 - Ruim', 
                3: '3 - Razoável',
                4: '4 - Bom',
                5: '5 - Ótimo'
}

$(function() {
    // USP position 
    var USP = new google.maps.LatLng(-23.561399, -46.730789)
    var options = {
        center: USP, 
        disableDefaultUI: true,
        mapTypeIds: [
            google.maps.MapTypeId.ROADMAP,
            google.maps.MapTypeId.SATELLITE
        ],
        panControl: true,
        zoom: 15,
        zoomControl: true,
        mapTypeControl: true,
        mapTypeControlOptions: {
            style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
            position: google.maps.ControlPosition.LEFT_BOTTOM
        },
    };
    var canvas = $("#map-canvas").get(0)
    map = new google.maps.Map(canvas, options)

    google.maps.event.addListenerOnce(map, "idle", configure)

    // setup heatmap for crime data
    pointArray = new google.maps.MVCArray(heatmapData)
    heatmap = new google.maps.visualization.HeatmapLayer({
      data: pointArray,
      radius: 15,
      dissipating: true
    });

    // hide and show of login and register panel 
    if($("#login-panel").length) { // or register 
        $("#register-link").click(toggleLoginReg)
        $("#login-link").click(toggleLoginReg)

        $("#register-form").submit(function(e) { 
            var password = $(this).find("#inputPassword").val()
            var password2 = $(this).find("#inputPassword2").val()
            var email = $(this).find("#inputEmail").val()
            var re = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@(?:[a-zA-Z0-9\-]+\.)?usp\.br$/i
            if(!re.test(email)) {
                $(".s-msgs").remove()
                $("#c-errors").text('Utilize o email acadêmico da USP.')
                return false
            }
            if(passwd != passwd2) {
                $(".s-msgs").remove()
                $("#c-errors").text('Senhas não conferem.')
                return false 
            }
            if(passwd.length < 10) {
                $(".s-msgs").remove()
                $("#c-errors").text('Senha deve ter pelo menos 10 dígitos.')
                return false
            }
        });
    }

    if($("#user-panel").length) { // proceed if user panel is showing 
        $("#see-crimes").click(toggleCrime)
        $("#see-filter").click(toggleFilter)
        $("#score-filter").on('change', updateResidences)

        $("#user-panel-header").click(function(){
            $("#user-resize").toggleClass("glyphicon-minus-sign")
            $("#user-panel-name").fadeToggle("fast")
            $("#user-panel-body").fadeToggle("fast")
            $("#logout").fadeToggle("fast")
            $("#user-resize").toggleClass("glyphicon-plus-sign")
        })
        // show modal when a given review-row is clicked
        $(".reviews-table").on('click', '.review-row', function() {
            var params = {
                rev_id: $(this).data('revid')
            }
            $(".modal-dialog").remove()
            $.get("/review", params, function(response) {
                $("#review-modal").append(response)
            });
            $("#review-modal").modal('show')
        });

        if($("#reviews-body").children().length) { // is there any review to show?
            pages = getPageState("reviews")
            // display is initally none so it doesn't load without being hidden 
            $("#reviews-body").css("display","")
            showPage("reviews", pages.curr_page, pages.curr_page, pages.first_page, pages.last_page)
            
            $("#previous-reviews-page").click(function() { 
                pages.curr_page = showPage("reviews", pages.curr_page, pages.curr_page+1, pages.first_page, pages.last_page)
            });
            $("#next-reviews-page").click(function() {
                pages.curr_page = showPage("reviews", pages.curr_page, pages.curr_page-1, pages.first_page, pages.last_page)
            });
        }
    }
});


// hide or show crime data on the map 
function toggleCrime() {
    heatmap.setMap(heatmap.getMap() ? null : map)
}

// hide or show score filter on the user menu 
function toggleFilter() {
    $("#score-filter-value").toggle()
    $("#score-filter").toggle() 
    if($("#score-filter").css("display") != "none") // update only when asked 
        updateResidences()
    else
        update(0)
}

// update residences on the map to those with a given score
function updateResidences() { 
    var score_val = $("#score-filter").val()
    $("#score-filter-value").text(": " + score_names[score_val])
    update(score_val) 
}

// hide login-show register and vice-versa 
function toggleLoginReg() { 
    $("#login").toggle()
    $("#register").toggle()
}

function controlPages(ident) {
    // .....
}

// function to control next and previous of user reviews
// curr: int, current page
// next: int, next page
// last: int, number of the last page
// ident: identifier for the page group, for instance, "reviews" or "map-reviews"
//        class for page identifier should be ident-page-page_num, e.g. "map-reviews-page-3"
function showPage(ident, curr, next, first, last) {
    // going forward
    if(curr > next && curr > last) {
        $("." + ident + "-page-" + curr).hide()
        curr--
        $("."  + ident + "-page-" + next).show()
        $("#previous-" + ident + '-page').attr("class", "previous enabled")
        if(curr == 0) { // curr hit last page
                $("." + ident + "-page-" + curr).show()
                $("#next-" + ident + '-page').attr("class", "next disabled")
        }
    }
    // going back 
    if(curr < next && curr < first) {
        $("."  + ident + "-page-" + curr).hide()
        curr++
        $("."  + ident + "-page-" + next).show()
        $("#next-" + ident + '-page').attr("class", "next enabled")
        if(curr == first) { // curr hit first page, disable previous button 
            $("#previous-" + ident + '-page').attr("class", "previous disabled")
        }
    }
    // just show, don't move  
    if(curr == next)
        $("." + ident + "-page-" + curr).show()

    // only one page, disable next button
    if(last == first)  
        $("#next-" + ident + '-page').attr("class", "next disabled")
    return curr
}


function getPageState(table_id) {
    var pages = {
        curr_page: $("#" + table_id + "-body").children().first().data('page'),
        first_page: $("#" + table_id + "-body").children().first().data('page'),
        last_page: 0
    }
    return pages
}


function appendRevRow(table_id, maxrows, data, pages) {
    // Table is a stack whose top element is the first item in the first page;
    // first item has biggest index;

    // get top item and its index, id and page  
    var topind = $("#" + table_id + "-body tr:first-child").data('item')
    var topid = $("#" + table_id + "-body tr:first-child").data('id')
    var toppage = $("#" + table_id + "-body tr:first-child").data('page')

    // insert item+1 at the top of either page or page+1
    // is there room in this page? 
    n_rows = $("." + table_id + '-page-' + toppage).length
    if(n_rows >= maxrows)
        new_page = toppage+1 // no, add one page
    else
        new_page = toppage
    // get a copy of the row   
    var row = $("#" + table_id + "-body tr:first-child").clone()
    // set the right page and item index
    row.attr('data-page', new_page)
    row.attr('data-item', topind+1)
    row.attr('data-revid', data[data.length-1]) 
    
    row.removeClass(table_id+'-page-'+ toppage).addClass(table_id+'-page-'+new_page)
    // set the new columns
    row.children().each(function(ind) {
        $(this).text(data[ind])
    })
    if(topid == -1) // empty table, remove empty placeholder
        $("#" + table_id + "-body tr:first-child").remove()

    $("#" + table_id + '-body').prepend(row)
    $("." + table_id + '-page-' + (new_page-1)).hide() // <--- fix to hide bottom not entire page??
    
    pages.curr_page = new_page
    pages.first_page = new_page
}


// setup event listeners on the map and show all residences
function configure() {
    google.maps.event.addListener(map, 'rightclick', function(e) {
        optionsDialog(e)
    });
    google.maps.event.addListener(map, "dragend", function() {
        $(".right-panel" ).css("opacity", "1.0") 
        $("#uspeda-logo" ).css("opacity", "1.0")  
    });
    google.maps.event.addListener(map, "zoom_changed", function() {
    
    });
    google.maps.event.addListener(map, "dragstart", function() {
        $(".right-panel" ).css("opacity", "0.2") 
        $("#uspeda-logo" ).css("opacity", "0.2") 
    });
    update(0) // 0 == no filter 
}

// right click on the map calls this
// setup infoWindow for the user 
function optionsDialog(e) {
    if(infowindow)
        infowindow.close()
    var params = {}
    $.get("/options", params, function(response) {
        infowindow = new google.maps.InfoWindow({
            content: response
        });
        infowindow.setPosition(e.latLng)
        infowindow.open(map)

        google.maps.event.addListener(infowindow, 'domready', function() { 
            $("#inputZipcode").mask('00000-000')

            $("#inputOwner").focus()

            $("#review-form").submit(function(e2) {
                e2.preventDefault()
                var params = {
                    lat: e.latLng.lat(),
                    lng: e.latLng.lng(),
                    owner: $("#inputOwner").val(),
                    res_name: $("#inputResName").val(),
                    zipcode: $("#inputZipcode").val(),
                    address: $("#inputAddress").val(),
                    score: parseInt($('select[name=inputScore]').val()),
                    review_text: $("#inputRevText").val()
                }
                $.ajax({
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify(params),
                    dataType: 'json',
                    url: '/add_review',
                    success: function (response) {
                        var review = response.review
                        if(review.new_res)
                            var residence = {
                                resname: review.res_name, 
                                owner: review.owner, 
                                lat: review.lat, 
                                lng: review.lng
                            }
                            addMarker(residence)
                        pages = getPageState('reviews');  
                        appendRevRow('reviews', 5, [residence.resname, residence.owner, review.date, review.score, review.rev_id], pages)
                    }
                });
                infowindow.close()
            });

            $("#crime-form").submit(function(e2) {
                e2.preventDefault();
                var params = {
                    lat: e.latLng.lat(),
                    lng: e.latLng.lng(),
                    weight: parseInt($('select[name=inputCrimeWeight]').val())
                }
                $.ajax({
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify(params),
                    dataType: 'json',
                    url: '/add_crime',
                    success: function (response) {
                        crime = response.crime
                        point = {location: new google.maps.LatLng(crime.lat, crime.lng), weight: crime.weight}
                        addheatMapData(point)
                    }
                });
                infowindow.close()
            });
        });
    });
}

// remove all markers from the map
function removeMarkers() {
        for (var i = 0; i < markers.length; i++) {
            markers[i].setMap(null)
        }
        markers.length = 0
    }

// add a given marker (residence) and listen for a click
// which will setup a infoWindow dialog for the user
function addMarker(residence) {
    var myLatlng = new google.maps.LatLng(residence.lat, residence.lng)
    var marker = new google.maps.Marker({
        position: myLatlng,
        map: map,
        animation: google.maps.Animation.DROP,
        icon: {
            url: '/static/images/home_icon.png',
            size: new google.maps.Size(20, 20),
            scaledSize: new google.maps.Size(20, 20)
        },
        title: residence.name
    });
    google.maps.event.addListener(marker, 'click', function() {
        residenceDialog(marker)
    });
    markers.push(marker)
}

// setup the infoWindow for when the residence (marker) is clicked
// marker: the anchor marker clicked 
function residenceDialog(marker) {
    if(infowindow) // close the last infowindow if there is any 
        infowindow.close()

    var markerpos = marker.getPosition() 

    var params = {
        lat: markerpos.lat(),
        lng: markerpos.lng()
    }
    // retrieve content of infoWindow for a given residence point
    $.get("/residence", params, function(data) {
        infowindow = new google.maps.InfoWindow({
            content: data
        });
        infowindow.setPosition(markerpos)
        infowindow.open(map, marker)
        // domready is fired when the infowindow content is attached to the DOM
        google.maps.event.addListener(infowindow, 'domready', function() {
            $(".map-reviews-table").on('click', '.map-review-row', function() {
                var params = {
                    rev_id: $(this).data('revid')
                }
                $(".modal-dialog").remove()
                $.get("/review", params, function(response) {
                    $("#review-modal").append(response)
                });
                $("#review-modal").appendTo('body').modal('show') // move modal out of parent containers
            });

            $("#map-review-form").submit(function(e) {
                e.preventDefault()
                var params = {
                    lat: 0, // intentionally 0
                    lng: 0,
                    res_name: '_', // intentionally underscore, let the server do its magic. 
                    owner: '_',
                    address: '_',
                    zipcode: '_',
                    res_id: $("#mapResId").val(),
                    score: parseInt($('select[name=mapInputScore]').val()),
                    review_text: $("#mapInputRevText").val()
                }
                $.ajax({
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify(params),
                    dataType: 'json',
                    url: '/add_review',
                    success: function(response) {
                        $(".add-review-body").toggle()
                        review = response.review
                        var residence = {
                            res_name: review.res_name, 
                            owner: review.owner, 
                            lat: review.lat, 
                            lng: review.lng
                        }
                        pages = getPageState('reviews');
                        appendRevRow('reviews', 5, [residence.res_name, residence.owner, review.date, review.score, review.rev_id], pages)
                        mappages = getPageState('map-reviews');
                        appendRevRow('map-reviews', 5, [review.author, review.date, review.score, review.rev_id], mappages)
                    }
                });
            }); 
            if($("#map-reviews-body").children().length) { // is there any review to show?
                mappages = getPageState("map-reviews")
                // display is initally none so it doesn't load without being hidden 
                $("#map-reviews-body").css("display","")
                showPage("map-reviews", mappages.curr_page, mappages.curr_page, mappages.first_page, mappages.last_page)
                
                $("#previous-map-reviews-page").click(function() { 
                    mappages.curr_page = showPage("map-reviews", mappages.curr_page, mappages.curr_page+1, mappages.first_page, mappages.last_page)
                });
                $("#next-map-reviews-page").click(function() {
                    mappages.curr_page = showPage("map-reviews", mappages.curr_page, mappages.curr_page-1, mappages.first_page, mappages.last_page)
                });
            }
        });
    });
}

// push a crime data point to the heapMap point array
function addheatMapData(point) {
    pointArray.push(point)
}

// remove all crime data points
function removeheatMapData() {
    while(pointArray.length > 0) 
        pointArray.pop()
}   

// update the map and show only residences with a given score_val
// score_val: int, average score of a residence; 0 -> all residences
function update(score_val) {
    var params = { 
        avg_score: parseInt(score_val)
    }
    $.getJSON("/update", params, function(response) {
        var residence = response.residence 
        if(markers.length) 
            removeMarkers()
        for(var i = 0; i < residence.length; i++) {
            addMarker(residence[i])
        }

        crime = response.crime
        if(heatmapData.length)
            removeheatMapData()
        for(var i = 0; i < crime.length; i++) {
            var point = {
                location: new google.maps.LatLng(crime[i].lat, crime[i].lng), 
                weight: crime[i].weight
            }
            addheatMapData(point)
        }
    });
};
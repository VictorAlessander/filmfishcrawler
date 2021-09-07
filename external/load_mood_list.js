/*
    THIS IS THE SCRIPT WORKING IN THE WEBSITE TO LOAD THE CONTENT WHEN SCROLL EVENT IS TRIGGERED.
    UNDERSTAND THIS SCRIPT TO LOAD THE CONTENT TO BE SCRAPED FOR THE SPIDER
*/


/***SCROLL***/

var inprocess = false;
var cancelLoad = false;
$(window).on('scroll', function () {
if ($(window).scrollTop() + $(window).height() >= $(document).height() * 3 / 4 && !inprocess && !cancelLoad) {
    if (!$('#owl-demo  .drop-link.trending-lists').hasClass('active')) {
    var type = $('ul[role="tablist"] > li.active > a').attr('aria-controls');
    var count = countMoodlist;
    var id_subGenre = $('#sub-genres').find('.drop-link.active').data('id');
    $.ajax({
        method: 'post',
        url: '/movies/index/load-mood-lists',
        beforeSend: function () {
        inprocess = true;
        },
        data: 'type=' + type + '&offset=' + count + '&id=' + id_subGenre,
        success: function (data) {
        if (data != '') {
            $('.dib.full-page-w.film-card-row').append(data);
            slice_str();
            equalheight('.film-card-row .caption');
            countMoodlist += 9;
        } else {
            cancelLoad = true;
        }
        inprocess = false;
        }
    });
    }
}
});
